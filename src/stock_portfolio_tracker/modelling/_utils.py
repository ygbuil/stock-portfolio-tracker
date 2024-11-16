import numpy as np
import pandas as pd

from stock_portfolio_tracker.utils import PortfolioData, sort_at_end


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
            **{f"curr_qty_{position_type}": np.nan},
            **{f"trans_qty_{position_type}": df[f"trans_qty_{position_type}"].replace(np.nan, 0)},
        )
        .sort_values(["date"], ascending=False)
        .reset_index(drop=True)
    )

    iterator = list(reversed(df.index))

    # iterate from older to newer date
    for i in iterator:
        # if first day
        if i == iterator[0]:
            if np.isnan(df.loc[i, f"trans_qty_{position_type}"]):
                df.loc[i, f"curr_qty_{position_type}"] = 0
            else:
                df.loc[i, f"curr_qty_{position_type}"] = df.loc[
                    i,
                    f"trans_qty_{position_type}",
                ]
        else:
            df.loc[i, f"curr_qty_{position_type}"] = (
                df.loc[i, f"trans_qty_{position_type}"]
                + df.loc[i + 1, f"curr_qty_{position_type}"] * df.loc[i, f"split_{position_type}"]
            )

    return df.assign(
        **{f"trans_qty_{position_type}": df[f"trans_qty_{position_type}"].replace(0, np.nan)},
        **{
            f"curr_qty_{position_type}": df[f"curr_qty_{position_type}"].replace(
                0,
                np.nan,
            ),
        },
    )


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
def calc_curr_perc_gain(
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
                f"trans_val_{position_type}": lambda df: df[f"trans_val_{position_type}"].replace(
                    np.nan,
                    0,
                ),
            },
            **{
                f"curr_val_{position_type}": lambda df: df[f"curr_val_{position_type}"].replace(
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


def calc_assets_distribution(
    portfolio_model: pd.DataFrame,
    portfolio_data: PortfolioData,
    position_type: str,
) -> pd.DataFrame:
    """Calculate the percentage in size each asset represents to the overall portfolio as well as
    the value of each asset, both at end date.

    :param portfolio_model: Portfolio with curr_qty and curr_val for each asset.
    :param portfolio_data: Transactions history and other portfolio data.
    :param position_type: Type of position (asset, benchmark, etc).
    :return: Dataframe with the percentage and value of each asset at end date.
    """
    assets_distribution = portfolio_model[portfolio_model["date"] == portfolio_data.end_date][
        [
            "date",
            f"ticker_{position_type}",
            f"curr_qty_{position_type}",
            f"curr_val_{position_type}",
        ]
    ].reset_index(  # type: ignore[reportArgumentType]
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
                f"curr_val_{position_type}": round(  # type: ignore[reportCallIssue]
                    assets_distribution[f"curr_val_{position_type}"],  # type: ignore[reportArgumentType]
                    2,
                ),
            },
        )
        .sort_values([f"curr_val_{position_type}"], ascending=False)
        .reset_index(drop=True)
    )


def simulate_benchmark_proportional(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Simulate what would happen to benchmark if it was purchased/sold the same way as the asset
    in a proportional manner. Example: if curr_qty_asset is 100 and we buy 20 more, benchmark
    quantity is also increase by 20% (for example, from 60 to 72). If then 120 shares are sold
    (100%), 72 shares of benchmark are also sold (100%).

    :param df: Dataframe with transaction history of asset and Yahoo finance prices for asset and
    benchmark.
    :return: Dataframe with trans_qty_benchmark and trans_val_benchmark.
    """
    df = (
        df.sort_values(
            by=["date"],
            ascending=[False],
        )
        .reset_index(drop=True)
        .assign(
            trans_qty_benchmark=np.nan,
        )
    )

    iterator = list(reversed(df.index))
    latest_curr_qty_benchmark = 0
    ever_purchased = False

    for i in iterator:
        # if first time purchasing
        if not ever_purchased and not np.isnan(df.loc[i, "trans_qty_asset"]):
            df.loc[i, "trans_qty_benchmark"] = (
                -df.loc[i, "trans_val_asset"] / df.loc[i, "close_unadj_local_currency_benchmark"]
            )
            latest_curr_qty_benchmark += df.loc[i, "trans_qty_benchmark"]
            ever_purchased = True

        # if purchasing for a second or more time
        elif not np.isnan(df.loc[i, "trans_qty_asset"]):
            df.loc[i, "trans_qty_benchmark"] = (
                (df.loc[i, "trans_qty_asset"] + df.loc[i + 1, "curr_qty_asset"])
                / df.loc[i + 1, "curr_qty_asset"]
                - 1
            ) * latest_curr_qty_benchmark
            latest_curr_qty_benchmark += df.loc[i, "trans_qty_benchmark"]

    df["trans_val_benchmark"] = (
        -df["close_unadj_local_currency_benchmark"] * df["trans_qty_benchmark"]
    )

    return df
