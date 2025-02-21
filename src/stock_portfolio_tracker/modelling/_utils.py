import math

import numpy as np
import pandas as pd

from stock_portfolio_tracker.exceptions import UnsortedError
from stock_portfolio_tracker.utils import PositionType, TwrFreq, sort_at_end


def calc_curr_qty(
    df: pd.DataFrame,
    position_type: PositionType,
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
        df[f"trans_qty_{position_type.value}"].to_numpy(),
        df[f"split_{position_type.value}"].to_numpy(),
    )

    curr_qty = np.zeros(df_len := len(trans_qty), dtype=np.float64)

    for i in range(df_len):
        curr_qty[~i] = trans_qty[~i] + (0 if i == 0 else curr_qty[~i + 1] * split[~i])

    return df.assign(**{f"curr_qty_{position_type.value}": curr_qty})


@sort_at_end()
def calc_curr_val(
    df: pd.DataFrame,
    position_type: PositionType,
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
            f"curr_val_{position_type.value}": df[f"curr_qty_{position_type.value}"]
            * df[f"close_unadj_local_currency_{position_type.value}"],
        },
    )


@sort_at_end()
def calc_simple_return_daily(
    df: pd.DataFrame,
    position_type: PositionType,
    sorting_columns: list[dict[str, list[str | bool]]],  # noqa: ARG001
) -> pd.DataFrame:
    """Calculate on a daily basis:
        - Simple return since start, in absolute terms.
        - Simple return since start, in percentage terms.

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
    trans_val = df[f"trans_val_{position_type.value}"].to_numpy()
    curr_val = df[f"curr_val_{position_type.value}"].to_numpy()
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
            **{f"curr_abs_gain_{position_type.value}": np.round(money_out + money_in, 2)},
            **{
                f"curr_perc_gain_{position_type.value}": [
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
            f"trans_val_{position_type.value}",
            f"curr_val_{position_type.value}",
            f"curr_abs_gain_{position_type.value}",
            f"curr_perc_gain_{position_type.value}",
            "money_out",
            "money_in",
        ]
    ]

    df.loc[0, f"curr_abs_gain_{position_type.value}"] = 0
    df.loc[0, f"curr_perc_gain_{position_type.value}"] = 0

    return df


def calc_overall_returns(
    df: pd.DataFrame, position_type: PositionType
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate the yearly returns using the following approaches:
        - Simple returns.
        - Time weighted returns (TWR).

    Args:
        df: Portfolio data
        position_type: Type of position.

    Raises:
        UnsortedError: Unsorted input data.

    Returns:
        Returns
    """
    if not df["date"].is_monotonic_decreasing:
        raise UnsortedError

    simple_returns_yearly = calc_simple_return(df, position_type)

    twr_yearly = calc_twr(df, position_type, TwrFreq.YEARLY)

    twr_all = calc_twr(df, position_type, TwrFreq.ALL)
    twr_cagr = calc_cagr(twr_all[f"twr_{position_type.value}"].iloc[0], twr_all["year"].iloc[0])

    return simple_returns_yearly.merge(twr_yearly, on="year", how="left"), pd.DataFrame(
        {f"twr_cagr_{position_type.value}": [twr_cagr]}
    )


def calc_simple_return(df: pd.DataFrame, position_type: PositionType) -> pd.DataFrame:
    yearly_returns: dict[str, list[float]] = {
        "year": [],
        f"abs_gain_{position_type.value}": [],
        f"simple_return_{position_type.value}": [],
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
        yearly_returns[f"abs_gain_{position_type.value}"].append(
            round(money_in_end_of_period - money_out_beg_of_period_with_deposits, 2)
        )
        yearly_returns[f"simple_return_{position_type.value}"].append(
            round((money_in_end_of_period / money_out_beg_of_period_with_deposits - 1) * 100, 2)
        )

    return pd.DataFrame(yearly_returns)


def calc_twr(df: pd.DataFrame, position_type: PositionType, freq: TwrFreq) -> pd.DataFrame:
    """Calculate time weighted returns.

    Args:
        df: Dataframe with transactions and current portfolio value.
        position_type: Type of position.
        freq: Frequency on which to calculate TWR.

    Returns:
        Time weighted returns
    """
    twrs: dict[str, list[float]] = {
        "year": [],
        f"twr_{position_type.value}": [],
    }

    for _, group in (
        df.groupby(df["date"].dt.year, sort=False) if freq == TwrFreq.YEARLY else [(None, df)]
    ):
        returns_period = []

        trans_val, curr_val = (
            list(reversed(group[f"trans_val_{position_type.value}"].values)),
            list(reversed(group[f"curr_val_{position_type.value}"].values)),
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

        twrs["year"].append(
            group["date"].iloc[0].year
            if freq == TwrFreq.YEARLY
            else round((group["date"].iloc[0] - group["date"].iloc[-1]).days / 365, 2)
        )
        twrs[f"twr_{position_type.value}"].append(twr)

    return pd.DataFrame(twrs)


def calc_cagr(total_return: float, years: float) -> float:
    cagr: float = round(((total_return / 100 + 1) ** (1 / years) - 1) * 100, 2)
    return cagr
