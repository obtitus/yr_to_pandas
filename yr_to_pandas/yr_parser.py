"""This module provides functions to parse YR weather API responses into pandas DataFrames."""
# Standard library imports
import datetime
import logging

# data analysis libraries
import pandas as pd

# This library
from .datetime_helper import convert_utc_to_local

logger = logging.getLogger('yr.parser')


def parse_hourly_forecast_compact(res):
    """Convert a dictionary from locationforecast/2.0/compact to a flat pandas DataFrame.

    See :func:`get_hourly_forecast_compact(...) <yr_to_pandas.yr_examples.get_hourly_forecast_compact>`
    for example usage.
    """
    data = list()
    for item in res['properties']['timeseries']:
        time = convert_utc_to_local(item['time'])
        details = item['data']['instant']['details']

        row = dict(details)
        row['time'] = time

        for next_x_hours in ('next_1_hours', 'next_6_hours', 'next_12_hours'):
            if next_x_hours in item['data']:
                n = item['data'][next_x_hours]
                if 'details' in n and 'precipitation_amount' in n['details']:
                    details = n['details']
                    precipitation_amount = details['precipitation_amount']
                    row[next_x_hours + '_precipitation_amount'] = precipitation_amount

                symbol_code = n['summary']['symbol_code']

                row[next_x_hours + '_symbol_code'] = symbol_code

        data.append(row)

    df = pd.DataFrame(data)

    return df


def parse_nowcast(res):
    """Convert a dictionary from nowcast/2.0/compact to a flat pandas DataFrame.

    See :func:`get_nowcast(...) <yr_to_pandas.yr_examples.get_nowcast>` for example usage.
    """
    data = list()
    row = dict()
    for item in res['properties']['timeseries']:
        time = convert_utc_to_local(item['time'])

        details = item['data']['instant']['details']

        row.update(details)  # only the first result has all the items, keep the previous values when missing
        row['time'] = time
        data.append(dict(row))

    df = pd.DataFrame(data)

    return df


def parse_airquality(res):
    """Convert a dictionary from airqualityforecast/0.1 to a flat pandas DataFrame."""
    data = list()
    for item in res['data']['time']:
        # from pprint import pprint
        # pprint(item)
        time = convert_utc_to_local(item['from'])
        dt = convert_utc_to_local(item['to']) - time

        # Only capture the hourly records, which for some wierd reason have the same from and to timestamps.
        if dt != datetime.timedelta(0):
            logger.debug('Looking for hourly data, skipping %s - %s = %s', item['to'], item['from'], dt)
            continue

        row = dict()
        row['time'] = time
        for key, dct in item['variables'].items():
            new_key = key
            if 'units' in dct and dct['units'] != '1':
                new_key = '%s [%s]' % (key, dct['units'])

            row[new_key] = dct['value']

        data.append(row)

    df = pd.DataFrame(data)

    return df
