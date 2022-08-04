# Standard library imports
import datetime
import json
import locale
import logging
import os

# data analysis libraries
import pandas as pd
import pytz
# third party imports
import requests
# This library
from pandas_helper import pandas_concat_helper

logger = logging.getLogger('yr.client')

# constants
server = 'https://api.met.no/weatherapi/'
cache_dir = os.path.dirname(__file__)
headers = {'user-agent': 'python-yr/ob@cakebox.net',
           'Accept': 'application/json'}


def cached_yr_request(cache_filename, url, headers, params, **kwargs):
    """Calls the yr api, ensuring caching, 'Expires' and 'If-Modified-Since' headers are handled.

    Ensures Expires and If-Modified-Since yr headers are handled correctly to reduce load on server
    https://developer.yr.no/doc/GettingStarted/
     **kwargs are passed to requests.get
    Note: it is up to the application to ensure cache_filename is unique per unique request (i.e.
    different depending on url and location).
    From https://api.met.no/doc/TermsOfService: ensure you don't request a new location for every meter!
    """
    # ensure we are working on copy
    headers = dict(headers)
    params = dict(params)

    # Look for lat/lon/altitude to ensure we truncate as requested by API
    for key in params:
        # https://api.met.no/doc/TermsOfService, truncate coordinates to 4 decimals
        if key in ('lat', 'lon'):
            try:
                params[key] = '{:.4f}'.format(params[key])
            except ValueError: # probably not number
                pass
        # Truncate to integer
        if key == 'altitude':
            try:
                params[key] = '{:.0f}'.format(params[key])
            except ValueError: # probably not number
                pass

    # Look for previous call
    if os.path.exists(cache_filename):
        try:
            with open(cache_filename, 'r') as f:
                old = json.load(f)

            tzinfo = pytz.timezone('GMT')
            # not sure if this is needed/is a good idea,
            # force en_US in case computer is set to something else.
            # Yes this is bad coding. FIXME: Set computer to something else and see if it still matches locale.
            locale.setlocale(locale.LC_TIME, 'en_US.utf8')
            # Sat, 25 Dec 2021 08:03:41 GMT
            expires = datetime.datetime.strptime(old['Expires'], '%a, %d %b %Y %H:%M:%S %Z')
            expires = expires.replace(tzinfo=tzinfo)

            # get now, in the same timezone
            now = datetime.datetime.now(tzinfo)
            logger.debug('Now = %s (%s), Expires = %s (%s), Still valid? %s', now, now.tzinfo, expires, expires.tzinfo,
                         expires > now)
            if expires > now:
                logger.info('returning cached %s', cache_filename)
                return old

            headers['If-Modified-Since'] = old['Last-Modified']

        except json.decoder.JSONDecodeError:
            logger.warning('Invalid cache')

    logger.debug('Get %s(%s, %s)', url, headers, kwargs)
    req = requests.get(url, headers=headers, params=params, **kwargs)
    req.raise_for_status()

    if req.status_code == 304:
        logger.info('%s, No new data, returning cache %s', req.status_code, cache_filename)
        return old
    elif req.status_code == 203:
        logger.warning('YR deprication warning %s', url)

    res = json.loads(req.text)
    # keep these in cache for next time
    res['Expires'] = req.headers['Expires']
    res['Last-Modified'] = req.headers['Last-Modified']

    with open(cache_filename, 'w') as f:
        json.dump(res, f)

    return res


def convert_utc_to_local(time):
    """Convert UTC timestamp to local time without tzinfo"""
    # Probably a easier solution to this
    time = datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
    time = time.replace(tzinfo=pytz.UTC)
    time = time.astimezone()
    time = time.replace(tzinfo=None)

    return time


def get_hourly_forecast_compact(lat, lon):
    """Example usage of above function, get hourly forecast using locationforecast/2.0/compact with the given lat/lon

    returned as a pandas dataframe. Uses the scripts directory as the cache directory
    both to cache the previous request (in a .json file) and to keep history of previous results (in a .parquet file).
    """
    cache_filename = os.path.join(cache_dir, 'yr-locationforecast-%s-%s.json' % (lat, lon))
    historical_filename = os.path.join(cache_dir, 'yr-locationforecast-%s-%s.parquet' % (lat, lon))

    #
    payload = {'lat': lat, 'lon': lon}

    res = cached_yr_request(cache_filename, server + 'locationforecast/2.0/compact',
                            headers=headers, params=payload)

    data = list()
    for item in res['properties']['timeseries']:
        time = convert_utc_to_local(item['time'])
        details = item['data']['instant']['details']

        row = dict(details)
        row['time'] = time

        for next_x_hours in ('next_1_hours', 'next_6_hours', 'next_12_hours'):
            if next_x_hours in item['data']:
                n = item['data'][next_x_hours]
                if 'details' in n:
                    precipitation_amount = n['details']['precipitation_amount']
                    row[next_x_hours + '_precipitation_amount'] = precipitation_amount

                symbol_code = n['summary']['symbol_code']

                row[next_x_hours + '_symbol_code'] = symbol_code

        data.append(row)

    df_storage = None
    if os.path.exists(historical_filename):
        logger.info('Reading %s', historical_filename)
        df_storage = pd.read_parquet(historical_filename)

    df = pd.DataFrame(data)

    df = pandas_concat_helper(df, df_storage)

    logger.info('Writing %s', historical_filename)
    df.to_parquet(historical_filename)

    return df


def get_nowcast(lat, lon):
    """Example usage of above function, get hourly forecast using nowcast/2.0/compact with the given lat/lon

    returned as a pandas dataframe. Uses the scripts directory as the cache directory
    both to cache the previous request (in a .json file) and to keep history of previous results (in a .parquet file).

    https://api.met.no/weatherapi/nowcast/2.0/documentation
    """
    cache_filename = os.path.join(cache_dir, 'yr-nowcast-%s-%s.json' % (lat, lon))
    historical_filename = os.path.join(cache_dir, 'yr-nowcast-%s-%s.parquet' % (lat, lon))

    payload = {'lat': lat, 'lon': lon}

    res = cached_yr_request(cache_filename, server + 'nowcast/2.0/complete',
                            headers=headers, params=payload)

    data = list()
    row = dict()
    for item in res['properties']['timeseries']:
        time = convert_utc_to_local(item['time'])

        details = item['data']['instant']['details']

        row.update(details) # only the first result has all the items, keep the previous values when missing
        row['time'] = time
        data.append(dict(row))

    df_storage = None
    if os.path.exists(historical_filename):
        logger.info('Reading %s', historical_filename)
        df_storage = pd.read_parquet(historical_filename)

    df = pd.DataFrame(data)

    df = pandas_concat_helper(df, df_storage)

    logger.info('Writing %s', historical_filename)
    df.to_parquet(historical_filename)

    return df


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.debug('Hello world')

    LON = 10.83576
    LAT = 59.71949

    df = get_hourly_forecast_compact(lat=LAT, lon=LON)
    with pd.option_context('display.max_rows', 100, 'display.max_columns', None, 'display.width', 0):
        print(df)

    df = get_nowcast(lat=LAT, lon=LON)
    print(df)
