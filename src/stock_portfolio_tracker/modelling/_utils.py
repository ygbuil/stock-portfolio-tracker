import numpy as np
import pandas as pd

from stock_portfolio_tracker.utils import sort_at_end


def calc_curr_qty(
    df: pd.DataFrame,
    position_type: str,
) -> pd.DataFrame:
    """Calculate the daily quantity of share for an asset based on the buy / sale transactions and
    the stock splits.

    :param df: Dataframe containing dates, transaction quantity and stock splits.
    :param position_type: Type of position (asset, benchmark, etc).
    :return: Dataframe with the daily amount of shares hold.
    """
    df = (
        df.assign(
            **{f"curr_qty_{position_type}": np.float64(0)},
        )
        .sort_values(["date"], ascending=False)
        .reset_index(drop=True)
    )

    for i in (iterator := list(reversed(df.index))):
        # if first day
        if i == iterator[0]:
            df.loc[i, f"curr_qty_{position_type}"] = df.loc[
                i,
                f"trans_qty_{position_type}",
            ]
        else:
            df.loc[i, f"curr_qty_{position_type}"] = (
                df.loc[i, f"trans_qty_{position_type}"]
                + df.loc[i + 1, f"curr_qty_{position_type}"] * df.loc[i, f"split_{position_type}"]
            )

    return df


def calc_curr_val(df: pd.DataFrame, position_type: str) -> pd.DataFrame:
    """Calculate the daily total value of the asset.

    :param df: Dataframe containing daily asset quantity hold and daily price as in Yahoo Finance.
    :param position_type: Type of position (asset, benchmark, etc).
    :return: Dataframe with the daily position value.
    """
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
def calc_curr_gain(
    df: pd.DataFrame,
    position_type: str,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
    """Calculate or the overall portfolio, on a daily basis:
        - Absoulte gain since start.
        - Percentage gain since start.

    :param df: Dataframe with the daily portfolio value and the transaction value.
    :param position_type: Type of position (asset, benchmark, etc).
    :param sorting_columns: Columns to sort for each returned dataframe.
    :return: Dataframe with the absolute and percentage gain.
    """
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
                f"curr_val_{position_type}": lambda df: df[f"curr_val_{position_type}"].replace(
                    np.nan,
                    0,
                ),
            },
        )
    )

    curr_money_in = 0

    for i in (iterator := list(reversed(df.index))):
        if i == iterator[0]:
            df.loc[i, "money_out"] = min(df.loc[i, f"trans_val_{position_type}"], 0)
        else:
            df.loc[i, "money_out"] = df.loc[i + 1, "money_out"] + min(
                df.loc[i, f"trans_val_{position_type}"],
                0,
            )

        curr_money_in += max(0, df.loc[i, f"trans_val_{position_type}"])
        df.loc[i, "money_in"] = df.loc[i, f"curr_val_{position_type}"] + curr_money_in

    df = (  # type: ignore[reportAssignmentType]
        df.assign(
            **{f"curr_abs_gain_{position_type}": round(df["money_out"] + df["money_in"], 2)},
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
    )[["date", f"curr_abs_gain_{position_type}", f"curr_perc_gain_{position_type}"]]

    df.loc[0, f"curr_abs_gain_{position_type}"] = 0
    df.loc[0, f"curr_perc_gain_{position_type}"] = 0

    return df
