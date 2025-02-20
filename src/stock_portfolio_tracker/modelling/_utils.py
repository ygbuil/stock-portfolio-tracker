import math

import numpy as np
import pandas as pd

from stock_portfolio_tracker.exceptions import UnsortedError
from stock_portfolio_tracker.utils import TwrFreq, sort_at_end


def calc_curr_qty(
    df: pd.DataFrame,
    position_type: str,
) -> pd.DataFrame:
    """Calculate the daily quantity of share for an asset based on the buy / sale transactions and
    the stock splits.

    Args:
        df: Dataframe containing dates, transaction quantity and stock splits.
        position_type: Type of position (asset, benchmark, etc).

    Raises:
        UnsortedError: Unsorted input data.

    Returns:
        Dataframe with the daily amount of shares hold.
    """
    if not df["date"].is_monotonic_decreasing:
        raise UnsortedError

    trans_qty, split = (
        df[f"trans_qty_{position_type}"].to_numpy(),
        df[f"split_{position_type}"].to_numpy(),
    )

    curr_qty = np.zeros(df_len := len(trans_qty), dtype=np.float64)

    for i in range(df_len):
        curr_qty[~i] = trans_qty[~i] + (0 if i == 0 else curr_qty[~i + 1] * split[~i])

    return df.assign(**{f"curr_qty_{position_type}": curr_qty})


@sort_at_end()
def calc_curr_val(
    df: pd.DataFrame,
    position_type: str,
    sorting_columns: list[dict[str, list[str | bool]]],  # noqa: ARG001
) -> pd.DataFrame:
    """Calculate the daily total value of the asset.

    Args:
        df: Dataframe containing daily asset quantity hold and daily price as in Yahoo Finance.
        position_type: Type of position (asset, benchmark, etc).
        sorting_columns: Columns to sort for each returned dataframe.

    Returns:
        Dataframe with the daily position value.
    """
    return df.assign(
        **{
            f"curr_val_{position_type}": df[f"curr_qty_{position_type}"]
            * df[f"close_unadj_local_currency_{position_type}"],
        },
    )


@sort_at_end()
def calc_curr_gain(
    df: pd.DataFrame,
    position_type: str,
    sorting_columns: list[dict[str, list[str | bool]]],  # noqa: ARG001
) -> pd.DataFrame:
    """Calculate or the overall portfolio, on a daily basis:
        - Absoulte gain since start.
        - Percentage gain since start.

    Args:
        df: Dataframe with the daily portfolio value and the transaction value.
        position_type: Type of position (asset, benchmark, etc).
        sorting_columns: Columns to sort for each returned dataframe.

    Raises:
        UnsortedError: Unsorted input data.

    Returns:
        Dataframe with the absolute and percentage gain.
    """
    if not df["date"].is_monotonic_decreasing:
        raise UnsortedError

    curr_money_in = 0
    trans_val = df[f"trans_val_{position_type}"].to_numpy()
    curr_val = df[f"curr_val_{position_type}"].to_numpy()
    money_in = np.zeros(df_dim := len(trans_val), dtype=np.float64)
    money_out = np.zeros(df_dim, dtype=np.float64)

    for i in range(df_dim):
        money_out[~i] = (0 if i == 0 else money_out[~i + 1]) + min(trans_val[~i], 0)

        curr_money_in += max(0, trans_val[~i])
        money_in[~i] = curr_val[~i] + curr_money_in

    df = (
        df.assign(
            money_out=money_out,
            money_in=money_in,
            **{f"curr_abs_gain_{position_type}": np.round(money_out + money_in, 2)},
            **{
                f"curr_perc_gain_{position_type}": [
                    round((abs(x / y) - 1) * 100, 2) if y != 0 else np.float64(0)
                    for x, y in zip(money_in, money_out, strict=False)
                ],
            },
        )
        .groupby("date")
        .first()
        .reset_index()
    )[
        [
            "date",
            f"trans_val_{position_type}",
            f"curr_val_{position_type}",
            f"curr_abs_gain_{position_type}",
            f"curr_perc_gain_{position_type}",
            "money_out",
            "money_in",
        ]
    ]

    df.loc[0, f"curr_abs_gain_{position_type}"] = 0
    df.loc[0, f"curr_perc_gain_{position_type}"] = 0

    return df


def calc_yearly_returns(df: pd.DataFrame, position_type: str) -> pd.DataFrame:
    if not df["date"].is_monotonic_decreasing:
        raise UnsortedError

    simple_returns = calc_simple_return(df, position_type)

    twr = calc_twr(df, position_type, "yearly")

    return simple_returns.merge(twr, on="year", how="left")


def calc_simple_return(df: pd.DataFrame, position_type: str) -> pd.DataFrame:
    yearly_returns: dict[str, list[float]] = {
        "year": [],
        f"abs_gain_{position_type}": [],
        f"simple_return_{position_type}": [],
    }

    for _, group in df.groupby(df["date"].dt.year, sort=False):
        (
            money_in_end_of_period,
            money_in_beg_of_period,
            money_out_end_of_period,
            money_out_beg_of_period,
        ) = (
            group["money_in"].iloc[0],
            group["money_in"].iloc[-1],
            group["money_out"].iloc[0],
            group["money_out"].iloc[-1],
        )

        money_out_beg_of_period_with_deposits = money_in_beg_of_period + (
            abs(money_out_end_of_period) - abs(money_out_beg_of_period)
        )

        yearly_returns["year"].append(group["date"].iloc[0].year)
        yearly_returns[f"abs_gain_{position_type}"].append(
            round(money_in_end_of_period - money_out_beg_of_period_with_deposits, 2)
        )
        yearly_returns[f"simple_return_{position_type}"].append(
            round((money_in_end_of_period / money_out_beg_of_period_with_deposits - 1) * 100, 2)
        )

    return pd.DataFrame(yearly_returns)


def calc_twr(df: pd.DataFrame, position_type: str, freq: str) -> pd.DataFrame:
    twrs: dict[str, list[float]] = {
        "year": [],
        f"twr_{position_type}": [],
    }

    for _, group in (
        df.groupby(df["date"].dt.year, sort=False) if freq == TwrFreq.YEARLY.value else [(None, df)]
    ):
        returns_period = []

        trans_val, curr_val = (
            list(reversed(group[f"trans_val_{position_type}"].values)),
            list(reversed(group[f"curr_val_{position_type}"].values)),
        )

        for i in range(len(trans_val)):
            # if first day
            if i == 0:
                init_val = curr_val[i]
            # if final day
            elif i == len(trans_val) - 1:
                returns_period.append(curr_val[i] / init_val)
            # if transaction
            elif trans_val[i]:
                returns_period.append(curr_val[i - 1] / init_val)
                init_val = curr_val[i]

        twr = round((float(math.prod(returns_period) - 1) * 100), 2)

        twrs["year"].append(group["date"].iloc[0].year)
        twrs[f"twr_{position_type}"].append(twr)

    return pd.DataFrame(twrs)
