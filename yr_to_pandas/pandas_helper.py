import pandas as pd


def pandas_concat_helper(df1, df2, subset='time'):
    if df2 is not None:
        df1 = pd.concat([df2, df1], ignore_index=True)
        df1.drop_duplicates(subset='time', keep='last',
                           inplace=True, ignore_index=True)
        df1.sort_values(by='time', inplace=True)
    return df1
