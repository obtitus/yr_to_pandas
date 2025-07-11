"""
Provides a basic script to run the examples in `yr_examples.py`.

Intended use-case is to adapt yr_examples to your needs. Using as is will:
* fetch data for the specified latitude and longitude
* save the data in a local .parquet cache
"""
# Standard library imports
import logging

# This project
from yr_to_pandas import yr_examples

logger = logging.getLogger('yr.run')

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    lat = 59.71949
    lon = 10.83576
    logging.info('Getting hourly forecast and nowcast for %s, %s', lat, lon)
    yr_examples.get_hourly_forecast_compact(lat, lon)
    yr_examples.get_nowcast(lat, lon)
