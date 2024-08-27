import numpy as np
import pandas as pd


def calculate_current_quantity(group: pd.DataFrame, quantity_col_name: str, type: str) -> pd.DataFrame:
    group = (
        group.assign(
            current_quantity=np.nan,
            **{f"split_{type}": lambda df: df[f"split_{type}"].replace(0, 1)},
            **{quantity_col_name: group[quantity_col_name].replace(np.nan, 0)},
        )
        .sort_values(["date"], ascending=False)
        .reset_index(drop=True)
    )

    iterator = list(reversed(group.index))

    # iterate from older to newer date
    for i in iterator:
        # if first day
        if i == iterator[0]:
            if np.isnan(group.loc[i, quantity_col_name]):
                group.loc[i, "current_quantity"] = 0
            else:
                group.loc[i, "current_quantity"] = group.loc[i, quantity_col_name]
        else:
            # current_quantity = quantity_purchased_or_sold + (yesterdays_quantity * f"split_{type}") # noqa: ERA001 E501
            group.loc[i, "current_quantity"] = (
                group.loc[i, quantity_col_name]
                + group.loc[i + 1, "current_quantity"] * group.loc[i, f"split_{type}"]
            )

    return group.assign(
        **{f"split_{type}": lambda df: df[f"split_{type}"].replace(1, 0)},
        **{quantity_col_name: group[quantity_col_name].replace(0, np.nan)},
        current_quantity=lambda df: df["current_quantity"].replace(0, np.nan),
    ).rename(columns={"current_quantity": f"current_quantity_{type}"})


def calculate_current_value(df: pd.DataFrame, type: str) -> pd.DataFrame:
    return (
        df.assign(current_value=df[f"current_quantity_{type}"] * df[f"close_unadjusted_local_currency_{type}"])
        .rename(columns={"current_value": f"current_value_{type}"})
        .groupby(["date", f"ticker_{type}"])
        .first()  # get the latest current state when there are multiple transactions at the same day for a ticker # noqa: E501
        .sort_values(by=[f"ticker_{type}", "date"], ascending=[True, False])
        .reset_index()
    )


def calculate_current_percent_gain(
    df: pd.DataFrame,
    type: str,
    current_value_column_name: str,
) -> pd.DataFrame:
    df = sort_by_columns(
        df,
        ["date"],
        [False],
    ).assign(
        money_out=np.nan,
        money_in=np.nan,
        **{f"value_{type}": lambda df: df[f"value_{type}"].replace(np.nan, 0)},
        **{current_value_column_name: lambda df: df[current_value_column_name].replace(np.nan, 0)},
    )

    iterator = list(reversed(df.index))
    curr_money_in = 0

    for i in iterator:
        if i == iterator[0]:
            df.loc[i, "money_out"] = min(df.loc[i, f"value_{type}"], 0)
        else:
            df.loc[i, "money_out"] = df.loc[i + 1, "money_out"] + min(df.loc[i, f"value_{type}"], 0)

        curr_money_in += max(0, df.loc[i, f"value_{type}"])
        df.loc[i, "money_in"] = df.loc[i, current_value_column_name] + curr_money_in

    df = (
        df.assign(
            current_gain=lambda df: df["money_out"] + df["money_in"],
            current_percent_gain=lambda df: df.apply(
                lambda x: round((abs(x["money_in"] / x["money_out"]) - 1) * 100, 2)
                if x["money_out"] != 0
                else 0,
                axis=1,
            ),
        )
        .groupby("date")
        .first()
        .reset_index()
    )[["date", "current_gain", "current_percent_gain"]]

    df.loc[0, "current_gain"] = 0
    df.loc[0, "current_percent_gain"] = 0

    return sort_by_columns(
        df,
        ["date"],
        [False],
    )


def calculat_portfolio_current_positions(
    portfolio_model: pd.DataFrame,
    portfolio_data: pd.DataFrame,
    type: str
) -> pd.DataFrame:
    asset_portfolio_current_positions = portfolio_model[
        portfolio_model["date"] == portfolio_data.end_date
    ][["date", f"ticker_{type}", f"current_quantity_{type}", f"current_value_{type}"]].reset_index(drop=True)

    return (
        asset_portfolio_current_positions.assign(
            percent=round(
                asset_portfolio_current_positions[f"current_value_{type}"]
                / asset_portfolio_current_positions[f"current_value_{type}"].sum()
                * 100,
                2,
            ),
            current_position_value=round(
                asset_portfolio_current_positions[f"current_value_{type}"],
                2,
            ),
        )
        .sort_values([f"current_value_{type}"], ascending=False)
        .reset_index(drop=True)
    )

def calculate_benchmark_quantity(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df = sort_by_columns(
        df,
        ["date"],
        [False],
    ).assign(
        benchmark_quantity=np.nan,
    )

    iterator = list(reversed(df.index))
    latest_benchmark_current_quantity = 0

    for i in iterator:
        if i == iterator[0] and not np.isnan(df.loc[i, "quantity"]):
            df.loc[i, "benchmark_quantity"] = - df.loc[i, "value"]/df.loc[i, "close_unadjusted_local_currency"]
            latest_benchmark_current_quantity += df.loc[i, "benchmark_quantity"]
        elif not np.isnan(df.loc[i, "quantity"]) and np.isnan(df.loc[i+1, "current_quantity"]):
            df.loc[i, "benchmark_quantity"] = - df.loc[i, "value"]/df.loc[i, "close_unadjusted_local_currency"]
            latest_benchmark_current_quantity += df.loc[i, "benchmark_quantity"]
        elif not np.isnan(df.loc[i, "quantity"]):
            df.loc[i, "benchmark_quantity"] = ((df.loc[i, "quantity"] + df.loc[i+1, "current_quantity"])/df.loc[i+1, "current_quantity"] - 1)*latest_benchmark_current_quantity
            latest_benchmark_current_quantity += df.loc[i, "benchmark_quantity"]
    
    df["benchmark_value"] = -df["close_unadjusted_local_currency"]*df["benchmark_quantity"]

    return df


# def calculate_total_return_asset():


def sort_by_columns(
    df: pd.DataFrame,
    columns: list[str],
    ascending: list[bool],
) -> pd.DataFrame:
    return df.sort_values(
        by=columns,
        ascending=ascending,
    ).reset_index(drop=True)
