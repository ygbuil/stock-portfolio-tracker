import numpy as np
import pandas as pd

from stock_portfolio_tracker.utils import sort_at_end


def calculate_curr_qty(
    group: pd.DataFrame,
    quantity_col_name: str,
    position_type: str,
) -> pd.DataFrame:
    group = (
        group.assign(
            **{f"curr_qty_{position_type}": np.nan},
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
                group.loc[i, f"curr_qty_{position_type}"] = 0
            else:
                group.loc[i, f"curr_qty_{position_type}"] = group.loc[i, quantity_col_name]
        else:
            # f"curr_qty_{position_type}" = quantity_purchased_or_sold + (yesterdays_quantity * f"split_{position_type}") # noqa: E501
            group.loc[i, f"curr_qty_{position_type}"] = (
                group.loc[i, quantity_col_name]
                + group.loc[i + 1, f"curr_qty_{position_type}"]
                * group.loc[i, f"split_{position_type}"]
            )

    return group.assign(
        **{f"split_{position_type}": group[f"split_{position_type}"].replace(1, 0)},
        **{quantity_col_name: group[quantity_col_name].replace(0, np.nan)},
        **{
            f"curr_qty_{position_type}": group[f"curr_qty_{position_type}"].replace(
                0,
                np.nan,
            ),
        },
    )


def calculate_curr_val(df: pd.DataFrame, position_type: str) -> pd.DataFrame:
    return (
        df.assign(
            curr_val=df[f"curr_qty_{position_type}"]
            * df[f"close_unadj_local_currency_{position_type}"],
        )
        .rename(columns={"curr_val": f"curr_val_{position_type}"})
        .groupby(["date", f"ticker_{position_type}"])
        .first()  # get the latest current state when there are multiple transactions at the same day for a ticker # noqa: E501
        .sort_values(by=[f"ticker_{position_type}", "date"], ascending=[True, False])
        .reset_index()
    )


@sort_at_end()
def calculate_curr_perc_gain(
    df: pd.DataFrame,
    position_type: str,
    curr_val_column_name: str,
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
                curr_val_column_name: lambda df: df[curr_val_column_name].replace(
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
        df.loc[i, "money_in"] = df.loc[i, curr_val_column_name] + curr_money_in

    df = (
        df.assign(
            **{f"curr_gain_{position_type}": df["money_out"] + df["money_in"]},
            **{
                f"curr_perc_gain_{position_type}": np.where(
                    df["money_out"] != 0,
                    round((abs(df["money_in"] / df["money_out"]) - 1) * 100, 2),
                    0,
                ),
            },
        )
        .groupby("date")
        .first()
        .reset_index()
    )[["date", f"curr_gain_{position_type}", f"curr_perc_gain_{position_type}"]]

    df.loc[0, f"curr_gain_{position_type}"] = 0
    df.loc[0, f"curr_perc_gain_{position_type}"] = 0

    return df


def calculat_assets_distribution(
    portfolio_model: pd.DataFrame,
    portfolio_data: pd.DataFrame,
    position_type: str,
) -> pd.DataFrame:
    assets_distribution = portfolio_model[portfolio_model["date"] == portfolio_data.end_date][
        [
            "date",
            f"ticker_{position_type}",
            f"curr_qty_{position_type}",
            f"curr_val_{position_type}",
        ]
    ].reset_index(
        drop=True,
    )

    return (
        assets_distribution.assign(
            percent=round(
                assets_distribution[f"curr_val_{position_type}"]
                / assets_distribution[f"curr_val_{position_type}"].sum()
                * 100,
                2,
            ),
            **{
                f"curr_val_{position_type}": round(
                    assets_distribution[f"curr_val_{position_type}"],
                    2,
                ),
            },
        )
        .sort_values([f"curr_val_{position_type}"], ascending=False)
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
    latest_curr_qty_benchmark = 0

    for i in iterator:
        if (
            i == iterator[0]
            and not np.isnan(df.loc[i, "quantity_asset"])
            or not np.isnan(df.loc[i, "quantity_asset"])
            and np.isnan(df.loc[i + 1, "curr_qty_asset"])
        ):
            df.loc[i, "quantity_benchmark"] = (
                -df.loc[i, "value_asset"] / df.loc[i, "close_unadj_local_currency_benchmark"]
            )
            latest_curr_qty_benchmark += df.loc[i, "quantity_benchmark"]
        elif not np.isnan(df.loc[i, "quantity_asset"]):
            df.loc[i, "quantity_benchmark"] = (
                (df.loc[i, "quantity_asset"] + df.loc[i + 1, "curr_qty_asset"])
                / df.loc[i + 1, "curr_qty_asset"]
                - 1
            ) * latest_curr_qty_benchmark
            latest_curr_qty_benchmark += df.loc[i, "quantity_benchmark"]

    df["value_benchmark"] = -df["close_unadj_local_currency_benchmark"] * df["quantity_benchmark"]

    return df
