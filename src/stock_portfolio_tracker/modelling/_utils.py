import math

import numpy as np
import pandas as pd

from stock_portfolio_tracker.exceptions import UnsortedError
from stock_portfolio_tracker.utils import Freq, PositionType, sort_at_end


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
            **{  # type: ignore
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


def calc_overall_returns(df: pd.DataFrame, position_type: PositionType) -> pd.DataFrame:
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

    simple_returns_all = pd.concat(
        [
            calc_simple_return(df, position_type, Freq.ALL),
            calc_simple_return(df, position_type, Freq.YEARLY),
        ],
        axis=0,
    ).reset_index(drop=True)
    twr_all = pd.concat(
        [calc_twr(df, position_type, Freq.ALL), calc_twr(df, position_type, Freq.YEARLY)], axis=0
    ).reset_index(drop=True)

    portfolio_age = round((df["date"].iloc[0] - df["date"].iloc[-1]).days / 365, 2)
    simple_returns_cagr, twr_cagr = (
        calc_cagr(
            simple_returns_all[
                (simple_returns_all["year"] == "all_time")
                & (simple_returns_all["unit_type"] == "perc")
            ][f"return_{position_type.value}"].iloc[0],
            portfolio_age,
        ),
        calc_cagr(
            twr_all[twr_all["year"] == "all_time"][f"return_{position_type.value}"].iloc[0],
            portfolio_age,
        ),
    )

    return pd.concat(
        [
            simple_returns_all,
            twr_all,
            pd.DataFrame(
                {
                    "year": ["all_time"],
                    "metric_type": ["simple_return"],
                    "unit_type": ["cagr"],
                    f"return_{position_type.value}": [simple_returns_cagr],
                }
            ),
            pd.DataFrame(
                {
                    "year": ["all_time"],
                    "metric_type": ["twr"],
                    "unit_type": ["cagr"],
                    f"return_{position_type.value}": [twr_cagr],
                }
            ),
        ],
        axis=0,
    ).reset_index(drop=True)


def calc_simple_return(df: pd.DataFrame, position_type: PositionType, freq: Freq) -> pd.DataFrame:
    simple_returns: dict[str, list[str | int | float]] = {
        "metric_type": [],
        "unit_type": [],
        "year": [],
        f"return_{position_type.value}": [],
    }

    for _, group in (
        df.groupby(df["date"].dt.year, sort=False) if freq == Freq.YEARLY else [(None, df)]
    ):
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

        simple_returns["metric_type"].extend(["simple_return"] * 2)
        simple_returns["year"].extend(
            [group["date"].iloc[0].year] * 2 if freq == Freq.YEARLY else ["all_time"] * 2
        )

        simple_returns["unit_type"].append("abs")
        simple_returns[f"return_{position_type.value}"].append(
            round(money_in_end_of_period - money_out_beg_of_period_with_deposits, 2)
        )

        simple_returns["unit_type"].append("perc")
        simple_returns[f"return_{position_type.value}"].append(
            round((money_in_end_of_period / money_out_beg_of_period_with_deposits - 1) * 100, 2)
        )

    return pd.DataFrame(simple_returns)


def calc_twr(df: pd.DataFrame, position_type: PositionType, freq: Freq) -> pd.DataFrame:
    """Calculate time weighted returns.

    Args:
        df: Dataframe with transactions and current portfolio value.
        position_type: Type of position.
        freq: Frequency on which to calculate TWR.

    Returns:
        Time weighted returns
    """
    twrs: dict[str, list[str | int | float]] = {
        "metric_type": [],
        "unit_type": [],
        "year": [],
        f"return_{position_type.value}": [],
    }

    for _, group in (
        df.groupby(df["date"].dt.year, sort=False) if freq == Freq.YEARLY else [(None, df)]
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

        twrs["metric_type"].append("twr")
        twrs["unit_type"].append("perc")
        twrs["year"].append(group["date"].iloc[0].year if freq == Freq.YEARLY else "all_time")
        twrs[f"return_{position_type.value}"].append(twr)

    return pd.DataFrame(twrs)


def calc_cagr(total_return: float, years: float) -> float:
    """Calculate the compound annual growth rate (CAGR).

    Args:
        total_return: Total return in percentage between start and end.
        years: Number of years.

    Returns:
        CAGR in percentage.
    """
    cagr: float = round(((total_return / 100 + 1) ** (1 / years) - 1) * 100, 2)
    return cagr
