"""Misc pandas helper functions."""
# Standard library imports
import logging
import os

# data analysis libraries
import pandas as pd

logger = logging.getLogger('yr.pandas')


def pandas_concat(df1, df2, subset='time'):
    """Return a concatenated dataframe, duplicate subset columns uses values from df2."""
    if df2 is not None:
        df1 = pd.concat([df2, df1], ignore_index=True)
        df1.drop_duplicates(subset='time', keep='last',
                            inplace=True, ignore_index=True)
        df1.sort_values(by='time', inplace=True)
    return df1


def keep_history(historical_filename, df):
    """Load (if it exists) and save pandas.DataFrame df to historical_filename."""
    df_storage = None
    if os.path.exists(historical_filename):
        logger.info('Reading %s', historical_filename)
        df_storage = pd.read_parquet(historical_filename)

    df = pandas_concat(df, df_storage)
    logger.info('Writing %s', historical_filename)
    df.to_parquet(historical_filename)

    return df
