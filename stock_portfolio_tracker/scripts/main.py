import pandas as pd
import numpy as np

# Sample DataFrame
data = {
    'A': ['foo', 'foo', 'foo', 'bar', 'bar'],
    'B': [1, 2, np.nan, np.nan, np.nan]
}
df = pd.DataFrame(data)

# Custom sum function
def custom_sum(series):
    if series.isna().all():
        return np.nan
    else:
        return series.sum(skipna=True)

# Group by column 'A' and apply custom sum function on column 'B'
result = df.groupby('A')['B'].agg(lambda x: np.nan if x.isna().all() else x.sum(skipna=True)).reset_index()

print(result)
