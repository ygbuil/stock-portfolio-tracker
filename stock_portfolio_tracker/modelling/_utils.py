import numpy as np
import pandas as pd

from stock_portfolio_tracker.utils import sort_at_end


def calculate_current_quantity(
    group: pd.DataFrame,
    quantity_col_name: str,
    position_type: str,
) -> pd.DataFrame:
    group = (
        group.assign(
            current_quantity=np.nan,
            **{f"split_{position_type}": lambda df: df[f"split_{position_type}"].replace(0, 1)},
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
            # current_quantity = quantity_purchased_or_sold + (yesterdays_quantity * f"split_{position_type}") # noqa: ERA001 E501
            group.loc[i, "current_quantity"] = (
                group.loc[i, quantity_col_name]
                + group.loc[i + 1, "current_quantity"] * group.loc[i, f"split_{position_type}"]
            )

    return group.assign(
        **{f"split_{position_type}": lambda df: df[f"split_{position_type}"].replace(1, 0)},
        **{quantity_col_name: group[quantity_col_name].replace(0, np.nan)},
        current_quantity=lambda df: df["current_quantity"].replace(0, np.nan),
    ).rename(columns={"current_quantity": f"current_quantity_{position_type}"})


def calculate_current_value(df: pd.DataFrame, position_type: str) -> pd.DataFrame:
    return (
        df.assign(
            current_value=df[f"current_quantity_{position_type}"]
            * df[f"close_unadjusted_local_currency_{position_type}"],
        )
        .rename(columns={"current_value": f"current_value_{position_type}"})
        .groupby(["date", f"ticker_{position_type}"])
        .first()  # get the latest current state when there are multiple transactions at the same day for a ticker # noqa: E501
        .sort_values(by=[f"ticker_{position_type}", "date"], ascending=[True, False])
        .reset_index()
    )


@sort_at_end()
def calculate_current_percent_gain(
    df: pd.DataFrame,
    position_type: str,
    current_value_column_name: str,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
    df = (
        df.sort_values(
            by=["date"],
            ascending=[False],
        )
        .reset_index(drop=True)
        .assign(
            money_out=np.nan,
            money_in=np.nan,
            **{
                f"value_{position_type}": lambda df: df[f"value_{position_type}"].replace(
                    np.nan,
                    0,
                ),
            },
            **{
                current_value_column_name: lambda df: df[current_value_column_name].replace(
                    np.nan,
                    0,
                ),
            },
        )
    )

    iterator = list(reversed(df.index))
    curr_money_in = 0

    for i in iterator:
        if i == iterator[0]:
            df.loc[i, "money_out"] = min(df.loc[i, f"value_{position_type}"], 0)
        else:
            df.loc[i, "money_out"] = df.loc[i + 1, "money_out"] + min(
                df.loc[i, f"value_{position_type}"],
                0,
            )

        curr_money_in += max(0, df.loc[i, f"value_{position_type}"])
        df.loc[i, "money_in"] = df.loc[i, current_value_column_name] + curr_money_in

    df = (
        df.assign(
            **{f"current_gain_{position_type}": lambda df: df["money_out"] + df["money_in"]},
            **{
                f"current_percent_gain_{position_type}": lambda df: df.apply(
                    lambda x: round((abs(x["money_in"] / x["money_out"]) - 1) * 100, 2)
                    if x["money_out"] != 0
                    else 0,
                    axis=1,
                ),
            },
        )
        .groupby("date")
        .first()
        .reset_index()
    )[["date", f"current_gain_{position_type}", f"current_percent_gain_{position_type}"]]

    df.loc[0, f"current_gain_{position_type}"] = 0
    df.loc[0, f"current_percent_gain_{position_type}"] = 0

    return df


def calculat_asset_distribution(
    portfolio_model: pd.DataFrame,
    portfolio_data: pd.DataFrame,
    position_type: str,
) -> pd.DataFrame:
    asset_distribution = portfolio_model[portfolio_model["date"] == portfolio_data.end_date][
        [
            "date",
            f"ticker_{position_type}",
            f"current_quantity_{position_type}",
            f"current_value_{position_type}",
        ]
    ].reset_index(
        drop=True,
    )

    return (
        asset_distribution.assign(
            percent=round(
                asset_distribution[f"current_value_{position_type}"]
                / asset_distribution[f"current_value_{position_type}"].sum()
                * 100,
                2,
            ),
            current_position_value=round(
                asset_distribution[f"current_value_{position_type}"],
                2,
            ),
        )
        .sort_values([f"current_value_{position_type}"], ascending=False)
        .reset_index(drop=True)
    )


def calculate_quantity_benchmark(
    df: pd.DataFrame,
) -> pd.DataFrame:
    df = (
        df.sort_values(
            by=["date"],
            ascending=[False],
        )
        .reset_index(drop=True)
        .assign(
            quantity_benchmark=np.nan,
        )
    )

    iterator = list(reversed(df.index))
    latest_current_quantity_benchmark = 0

    for i in iterator:
        if (
            i == iterator[0]
            and not np.isnan(df.loc[i, "quantity_asset"])
            or not np.isnan(df.loc[i, "quantity_asset"])
            and np.isnan(df.loc[i + 1, "current_quantity_asset"])
        ):
            df.loc[i, "quantity_benchmark"] = (
                -df.loc[i, "value_asset"] / df.loc[i, "close_unadjusted_local_currency_benchmark"]
            )
            latest_current_quantity_benchmark += df.loc[i, "quantity_benchmark"]
        elif not np.isnan(df.loc[i, "quantity_asset"]):
            df.loc[i, "quantity_benchmark"] = (
                (df.loc[i, "quantity_asset"] + df.loc[i + 1, "current_quantity_asset"])
                / df.loc[i + 1, "current_quantity_asset"]
                - 1
            ) * latest_current_quantity_benchmark
            latest_current_quantity_benchmark += df.loc[i, "quantity_benchmark"]

    df["value_benchmark"] = (
        -df["close_unadjusted_local_currency_benchmark"] * df["quantity_benchmark"]
    )

    return df
