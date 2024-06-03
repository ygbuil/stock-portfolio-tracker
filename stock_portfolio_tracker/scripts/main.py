import pandas as pd
import numpy as np


# Function to calculate current quantity for a group
def _calculate_current_quantity(group):
    group["current_quantity"] = np.nan  # Initialize the new column

    for i in range(1, len(group) + 1):
        if i == 1:
            if np.isnan(group["quantity"].iloc[-i]):
                group["current_quantity"].iloc[-i] = 0
            else:
                group["current_quantity"].iloc[-i] = group["quantity"].iloc[-i]
        else:
            if (
                np.isnan(group["quantity"].iloc[-i])
                and group["stock_split"].iloc[-i] == 0
            ):
                group["current_quantity"].iloc[-i] = group["current_quantity"].iloc[
                    -i + 1
                ]
            elif (
                not np.isnan(group["quantity"].iloc[-i])
                and group["stock_split"].iloc[-i] == 0
            ):
                group["current_quantity"].iloc[-i] = (
                    group["current_quantity"].iloc[-i + 1] + group["quantity"].iloc[-i]
                )
            elif (
                np.isnan(group["quantity"].iloc[-i])
                and group["stock_split"].iloc[-i] != 0
            ):
                group["current_quantity"].iloc[-i] = (
                    group["current_quantity"].iloc[-i + 1]
                    * group["stock_split"].iloc[-i]
                )
            elif (
                not np.isnan(group["quantity"].iloc[-i])
                and group["stock_split"].iloc[-i] != 0
            ):
                group["current_quantity"].iloc[-i] = (
                    group["current_quantity"].iloc[-i + 1]
                    * group["stock_split"].iloc[-i]
                    + group["quantity"].iloc[-i]
                )
            else:
                raise NotImplementedError("Scenario not taken into account.")

    return group


# Sample DataFrame
data = {
    "stock_ticker": ["AAPL", "AAPL", "MSFT", "MSFT", "MSFT", "MSFT", "MSFT", "MSFT"],
    "stock_split": [0, 0, 0, 2, 0, 0, 0, 0],
    "quantity": [-1, 1, np.nan, np.nan, np.nan, 1, 4, np.nan],
}
df = pd.DataFrame(data)

# Apply the function to each group
df = (
    df.groupby("stock_ticker").apply(_calculate_current_quantity).reset_index(drop=True)
)

print(df)
