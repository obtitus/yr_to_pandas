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

from . import pandas_helper
# This library
from .datetime_helper import convert_utc_to_local

logger = logging.getLogger('yr.client')

# constants
server = 'https://api.met.no/weatherapi/'
cache_dir = os.path.dirname(__file__)
headers = {'user-agent': 'python-yr/ob@cakebox.net',
           'Accept': 'application/json'}


def cached_yr_request(cache_filename, url, headers, params, **kwargs):
    """Lowest level function, calls the yr api and returns a dictionary with the results.

    Ensures Expires and If-Modified-Since yr headers are handled correctly to reduce load on server
    https://developer.yr.no/doc/GettingStarted/

    Note: it is up to the application to ensure cache_filename is unique per unique request (i.e.
    different depending on url and location).
    From https://api.met.no/doc/TermsOfService: ensure you don't request a new location for every meter!

    Parameters
    ----------
    cache_filename : `str`
          Uses the given filename to cache the data.
    url : `str`
          Page url to visit
    headers : `dict`
          header sent to requests.get, ensure this has a custom 'user-agent' and 'Accept': 'application/json'
    params : `dict`
          params sent to requests.get, will typically contain at least 'lat' and 'lon', depends on url.
    **kwargs
          are passed to requests.get

    Returns
    -------
    dict
        Dictionary with results, depends on url, but will always contain 'Expires' and 'Last-Modified'.
        The result is also stored in cache_filename as json and will be returned directly if this function is
        called before the data has expired.
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
            logger.debug('reading cache %s', cache_filename)
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
    else:
        logger.debug('no cache, first time? %s', cache_filename)

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


def parse_hourly_forecast_compact(res):
    """Converts a dictionary from locationforecast/2.0/compact to a pandas DataFrame"""
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

    df = pd.DataFrame(data)

    return df


def get_hourly_forecast_compact(lat, lon):
    """Example for calling locationforecast/2.0/compact to get hourly forecast for a given lat/lon

    >>> df = get_hourly_forecast_compact(lat = 59.71949, lon = 10.83576)
    >>> df.keys()
    Index(['air_pressure_at_sea_level', 'air_temperature', 'cloud_area_fraction',
           'relative_humidity', 'wind_from_direction', 'wind_speed', 'time',
           'next_1_hours_precipitation_amount', 'next_1_hours_symbol_code',
           'next_6_hours_precipitation_amount', 'next_6_hours_symbol_code',
           'next_12_hours_symbol_code'],
          dtype='object')

    Uses the scripts directory as the cache directory
    both to cache the previous request (in a .json file) and to keep history of previous results (in a .parquet file).

    Parameters
    ----------
    lat : int
        latitude, will be rounded to 4 digits.
    lon : int
        longitude, will be rounded to 4 digits.

    Returns
    -------
    pandas.DataFrame
        returns a dataframe
    """
    cache_filename = os.path.join(cache_dir, 'yr-locationforecast-%s-%s.json' % (lat, lon))
    historical_filename = os.path.join(cache_dir, 'yr-locationforecast-%s-%s.parquet' % (lat, lon))

    #
    payload = {'lat': lat, 'lon': lon}

    res = cached_yr_request(cache_filename, server + 'locationforecast/2.0/compact',
                            headers=headers, params=payload)
    df = parse_hourly_forecast_compact(res)

    # Keep history
    df = pandas_helper.keep_history(historical_filename, df)

    return df


def parse_nowcast(res):
    """Converts a dictionary from nowcast/2.0/compact to a pandas DataFrame

    See :func:`get_nowcast(...) <yr_to_pandas.yr_client.get_nowcast>` for example usage
    """
    data = list()
    row = dict()
    for item in res['properties']['timeseries']:
        time = convert_utc_to_local(item['time'])

        details = item['data']['instant']['details']

        row.update(details) # only the first result has all the items, keep the previous values when missing
        row['time'] = time
        data.append(dict(row))

    df = pd.DataFrame(data)

    return df


def get_nowcast(lat, lon):
    """Example for calling nowcast/2.0/compact to get hourly forecast for a given lat/lon

    More information https://api.met.no/weatherapi/nowcast/2.0/documentation

    Uses the scripts directory as the cache directory
    both to cache the previous request (in a .json file) and to keep history of previous results (in a .parquet file).

    Parameters
    ----------
    lat : int
        latitude, will be rounded to 4 digits.
    lon : int
        longitude, will be rounded to 4 digits.

    Returns
    -------
    pandas.DataFrame
        returns a dataframe

    Examples
    --------
    >>> df = get_nowcast(lat = 59.71949, lon = 10.83576)
    >>> df.keys()
    Index(['air_temperature', 'relative_humidity', 'wind_from_direction',
           'wind_speed', 'wind_speed_of_gust', 'time', 'precipitation_rate'],
          dtype='object')


    """
    cache_filename = os.path.join(cache_dir, 'yr-nowcast-%s-%s.json' % (lat, lon))
    historical_filename = os.path.join(cache_dir, 'yr-nowcast-%s-%s.parquet' % (lat, lon))

    payload = {'lat': lat, 'lon': lon}

    res = cached_yr_request(cache_filename, server + 'nowcast/2.0/complete',
                            headers=headers, params=payload)
    df = parse_nowcast(res)

    df_storage = None
    if os.path.exists(historical_filename):
        logger.info('Reading %s', historical_filename)
        df_storage = pd.read_parquet(historical_filename)

    df = pandas_helper.pandas_concat(df, df_storage)

    logger.info('Writing %s', historical_filename)
    df.to_parquet(historical_filename)

    return df


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.debug('Hello world')

    import doctest
    doctest.testmod()

    LON = 10.83576
    LAT = 59.71949

    # df = get_hourly_forecast_compact(lat=LAT, lon=LON)
    # with pd.option_context('display.max_rows', 100, 'display.max_columns', None, 'display.width', 0):
    #     print(df)

    # df = get_nowcast(lat=LAT, lon=LON)
    # print(df)
