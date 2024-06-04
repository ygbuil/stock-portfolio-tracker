import pandas as pd
import numpy as np

# Sample DataFrame
data = {
    "A": ["a", "a", "foo", "foo", "foo", "bar", "bar"],
    "B": [np.nan, 10, np.nan, 2, 3, np.nan, np.nan],
}
df = pd.DataFrame(data)
df["B"] = df["B"].bfill().ffill()

print(df)
