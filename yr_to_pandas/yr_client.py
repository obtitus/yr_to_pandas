# Standard library imports
import datetime
import json
import locale
import logging
import os

import pytz
# third party imports
import requests

logger = logging.getLogger('yr.client')


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

    # set default Accept header
    headers['Accept'] = headers.get('Accept', 'application/json')

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
