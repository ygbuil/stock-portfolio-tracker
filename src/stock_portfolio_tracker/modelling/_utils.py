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
    df = df.sort_values(["date"], ascending=False).reset_index(drop=True)

    trans_qty, split = (
        df[f"trans_qty_{position_type}"].to_numpy(),
        df[f"split_{position_type}"].to_numpy(),
    )

    curr_qty = np.zeros(len(trans_qty), dtype=np.float64)

    for i in range(1, len(trans_qty) + 1):
        curr_qty[-i] = trans_qty[-i] + (0 if i == 1 else curr_qty[-(i - 1)] * split[-i])

    return df.assign(**{f"curr_qty_{position_type}": curr_qty})


@sort_at_end()
def calc_curr_val(
    df: pd.DataFrame,
    position_type: str,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
    """Calculate the daily total value of the asset.

    :param df: Dataframe containing daily asset quantity hold and daily price as in Yahoo Finance.
    :param position_type: Type of position (asset, benchmark, etc).
    :return: Dataframe with the daily position value.
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
    df = df.sort_values(by=["date"], ascending=[False]).reset_index(drop=True)

    curr_money_in = 0
    trans_val = df[f"trans_val_{position_type}"].to_numpy()
    curr_val = df[f"curr_val_{position_type}"].to_numpy()
    money_in = np.zeros(len(df), dtype=np.float64)
    money_out = np.zeros(len(df), dtype=np.float64)

    for i in range(1, len(df) + 1):
        money_out[-i] = (0 if i == 1 else money_out[-(i - 1)]) + min(trans_val[-i], 0)

        curr_money_in += max(0, trans_val[-i])
        money_in[-i] = curr_val[-i] + curr_money_in

    df = (  # type: ignore[reportAssignmentType]
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
    )[["date", f"curr_abs_gain_{position_type}", f"curr_perc_gain_{position_type}"]]

    df.loc[0, f"curr_abs_gain_{position_type}"] = 0
    df.loc[0, f"curr_perc_gain_{position_type}"] = 0

    return df
