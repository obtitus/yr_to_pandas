# Standard library imports
import logging
import os

# data analysis libraries
import pandas as pd

# This library
from . import pandas_helper, yr_client, yr_parser

logger = logging.getLogger('yr.client')

# constants
cache_dir = os.path.dirname(__file__)
server = 'https://api.met.no/weatherapi/'
headers = {'user-agent': 'python-yr/ob@cakebox.net'}


def get_hourly_forecast_compact(lat, lon):
    """Example for calling locationforecast/2.0/compact to get hourly forecast for a given lat/lon

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
    >>> df = get_hourly_forecast_compact(lat = 59.71949, lon = 10.83576)
    >>> df.keys()
    Index(['air_pressure_at_sea_level', 'air_temperature', 'cloud_area_fraction',
           'relative_humidity', 'wind_from_direction', 'wind_speed', 'time',
           'next_1_hours_precipitation_amount', 'next_1_hours_symbol_code',
           'next_6_hours_precipitation_amount', 'next_6_hours_symbol_code',
           'next_12_hours_symbol_code'],
          dtype='object')
    """
    cache_filename = os.path.join(cache_dir, 'yr-locationforecast-%s-%s.json' % (lat, lon))
    historical_filename = os.path.join(cache_dir, 'yr-locationforecast-%s-%s.parquet' % (lat, lon))

    #
    payload = {'lat': lat, 'lon': lon}

    res = yr_client.cached_yr_request(cache_filename, server + 'locationforecast/2.0/compact',
                                      headers=headers, params=payload)
    df = yr_parser.parse_hourly_forecast_compact(res)

    # Keep history
    df = pandas_helper.keep_history(historical_filename, df)

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

    res = yr_client.cached_yr_request(cache_filename, server + 'nowcast/2.0/complete',
                                      headers=headers, params=payload)
    df = yr_parser.parse_nowcast(res)

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
