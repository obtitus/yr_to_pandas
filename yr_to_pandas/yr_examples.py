"""
Provides basic examples to use the yr_to_pandas library.

Intended use-case is to adapt yr_examples to your needs. Using as is will:
* fetch data for the specified latitude and longitude
* save the data in a local .parquet cache
"""
# Standard library imports
import logging
import os

# This library
from . import pandas_helper, yr_client, yr_parser

logger = logging.getLogger('yr.client')

# constants
cache_dir = os.path.dirname(__file__)
server = 'https://api.met.no/weatherapi/'
headers = {'user-agent': 'python-yr/ob@cakebox.net'}


def get_hourly_forecast_compact(lat, lon):
    """Call locationforecast/2.0/compact to get hourly forecast for a given lat/lon.

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

    payload = {'lat': lat, 'lon': lon}

    # Get new data
    res = yr_client.cached_yr_request(cache_filename, server + 'locationforecast/2.0/compact',
                                      headers=headers, params=payload)
    df = yr_parser.parse_hourly_forecast_compact(res)

    # Keep history
    if not res['Cached']:
        df = pandas_helper.keep_history(historical_filename, df)
    else:
        logger.debug('Skipping write to %s as value is already cached', historical_filename)

    return df


def get_nowcast(lat, lon):
    """Call nowcast/2.0/compact to get hourly forecast for a given lat/lon.

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
    >>> sorted(df.keys())
    ['air_temperature', 'precipitation_rate', 'relative_humidity', 'time', 'wind_from_direction', 'wind_speed', 'wind_speed_of_gust']
    """
    cache_filename = os.path.join(cache_dir, 'yr-nowcast-%s-%s.json' % (lat, lon))
    historical_filename = os.path.join(cache_dir, 'yr-nowcast-%s-%s.parquet' % (lat, lon))

    payload = {'lat': lat, 'lon': lon}

    # Get new data
    res = yr_client.cached_yr_request(cache_filename, server + 'nowcast/2.0/complete',
                                      headers=headers, params=payload)
    df = yr_parser.parse_nowcast(res)

    # Keep history
    if not res['Cached']:
        df = pandas_helper.keep_history(historical_filename, df)
    else:
        logger.debug('Skipping write to %s as value is already cached', historical_filename)

    return df


def get_airquality(lat, lon, areaclass='grunnkrets'):
    """Call airqualityforecast/0.1 to get hourly forecast for a given lat/lon.

    More information https://api.met.no/weatherapi/airqualityforecast/0.1/documentation

    Uses the scripts directory as the cache directory
    both to cache the previous request (in a .json file) and to keep history of previous results (in a .parquet file).

    Parameters
    ----------
    lat : int
        latitude, will be rounded to 4 digits.
    lon : int
        longitude, will be rounded to 4 digits.
    arealclass=: str
        Size of the area, one of grunnkrets, fylke, kommune or delomrade

    Returns
    -------
    pandas.DataFrame
        returns a dataframe

    Examples
    --------
    >>> df = get_airquality(lat = 59.71949, lon = 10.83576)
    >>> df.keys()
    Index(['time', 'AQI', 'no2_concentration [ug/m3]', 'AQI_no2',
           'no2_nonlocal_fraction [%]', 'no2_nonlocal_fraction_seasalt [%]',
           'no2_local_fraction_traffic_exhaust [%]',
           'no2_local_fraction_traffic_nonexhaust [%]',
           'no2_local_fraction_shipping [%]', 'no2_local_fraction_heating [%]',
           'no2_local_fraction_industry [%]', 'pm10_concentration [ug/m3]',
           'AQI_pm10', 'pm10_nonlocal_fraction [%]',
           'pm10_nonlocal_fraction_seasalt [%]',
           'pm10_local_fraction_traffic_exhaust [%]',
           'pm10_local_fraction_traffic_nonexhaust [%]',
           'pm10_local_fraction_shipping [%]', 'pm10_local_fraction_heating [%]',
           'pm10_local_fraction_industry [%]', 'pm25_concentration [ug/m3]',
           'AQI_pm25', 'pm25_nonlocal_fraction [%]',
           'pm25_nonlocal_fraction_seasalt [%]',
           'pm25_local_fraction_traffic_exhaust [%]',
           'pm25_local_fraction_traffic_nonexhaust [%]',
           'pm25_local_fraction_shipping [%]', 'pm25_local_fraction_heating [%]',
           'pm25_local_fraction_industry [%]', 'o3_concentration [ug/m3]',
           'AQI_o3', 'o3_nonlocal_fraction [%]',
           'o3_nonlocal_fraction_seasalt [%]',
           'o3_local_fraction_traffic_exhaust [%]',
           'o3_local_fraction_traffic_nonexhaust [%]',
           'o3_local_fraction_shipping [%]', 'o3_local_fraction_heating [%]',
           'o3_local_fraction_industry [%]'],
          dtype='object')
    """
    cache_filename = os.path.join(cache_dir, 'yr-airquality-%s-%s.json' % (lat, lon))
    historical_filename = os.path.join(cache_dir, 'yr-airquality-%s-%s.parquet' % (lat, lon))

    payload = {'lat': lat, 'lon': lon, 'areaclass': areaclass}

    # Get new data
    res = yr_client.cached_yr_request(cache_filename, server + 'airqualityforecast/0.1',
                                      headers=headers, params=payload)

    # For description of each column:
    # cache_filename = os.path.join(cache_dir, 'yr-airquality-desc-%s-%s.json' % (lat, lon))
    # res = yr_client.cached_yr_request(cache_filename, server + 'airqualityforecast/0.1/aqi_description',
    #                                   headers=headers)

    df = yr_parser.parse_airquality(res)

    # Keep history
    if not res['Cached']:
        df = pandas_helper.keep_history(historical_filename, df)
    else:
        logger.debug('Skipping write to %s as value is already cached', historical_filename)

    return df


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    logger.debug('Hello world')

    import doctest
    doctest.testmod(raise_on_error=True, verbose=True)
