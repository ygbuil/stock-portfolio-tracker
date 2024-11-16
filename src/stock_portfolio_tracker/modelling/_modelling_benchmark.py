import numpy as np
import pandas as pd

from stock_portfolio_tracker.utils import PortfolioData, sort_at_end

from . import _utils as utils


@sort_at_end()
def model_benchmark_absolute(
    portfolio_data: PortfolioData,
    benchmark: pd.DataFrame,
    sorting_columns: list[dict],  # noqa: ARG001
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Model the benchmark as if the same transaction value purchased of an asset of the portfolio
    was purchased of the benchmark (in absoulte value). Under these simulation assumptions, the
    metrics calculated are, on a daily basis:
        - Value of the benchmark hold.
        - Percentage gain since start.

    :param portfolio_data: Transactions history and other portfolio data.
    :param benchmark: Benchmark historical data.
    :param sorting_columns: Columns to sort for each returned dataframe.
    :return: Dataframes with benchmark value and percentage gain.
    """
    benchmark_val_evolution_abs = _simulate_benchmark_absolute(benchmark, portfolio_data)

    benchmark_val_evolution_abs = utils.calc_curr_qty(
        benchmark_val_evolution_abs,
        "benchmark",
    )

    benchmark_val_evolution_abs = utils.calc_curr_val(
        benchmark_val_evolution_abs,
        "benchmark",
    ).assign(curr_val_benchmark=lambda df: round(df["curr_val_benchmark"], 2))

    benchmark_perc_evolution = utils.calc_curr_perc_gain(
        benchmark_val_evolution_abs[["date", "ticker_benchmark", "curr_val_benchmark"]]
        .merge(
            portfolio_data.transactions[["date", "trans_val_asset"]],
            how="left",
            on=["date"],
        )
        .assign(trans_val_asset=lambda df: df["trans_val_asset"].fillna(0))
        .rename(columns={"trans_val_asset": "trans_val_benchmark"}),
        "benchmark",
        sorting_columns=[{"columns": ["date"], "ascending": [False]}],
    )

    return benchmark_val_evolution_abs[["date", "curr_val_benchmark"]], benchmark_perc_evolution  # type: ignore[reportReturnType]


@sort_at_end()
def model_benchmark_proportional(
    portfolio_model: pd.DataFrame,
    benchmark: pd.DataFrame,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
    assets_vs_benchmark = pd.DataFrame(
        {
            "ticker_asset": [],
            "curr_perc_gain_asset": [],
            "curr_perc_gain_benchmark": [],
        },
    )

    for _, group in portfolio_model.groupby("ticker_asset"):
        group = benchmark[  # noqa: PLW2901
            [
                "date",
                "ticker_benchmark",
                "split_benchmark",
                "close_unadj_local_currency_benchmark",
            ]
        ].merge(
            group[
                [
                    "date",
                    "ticker_asset",
                    "trans_qty_asset",
                    "curr_qty_asset",
                    "close_unadj_local_currency_asset",
                    "trans_val_asset",
                ]
            ],
            how="left",
            on=["date"],
        )

        group = _simulate_benchmark_proportional(group)  # noqa: PLW2901

        group = utils.calc_curr_qty(  # noqa: PLW2901
            group,
            "benchmark",
        )

        group = utils.calc_curr_val(  # noqa: PLW2901
            group,
            "benchmark",
        )

        group = utils.calc_curr_val(  # noqa: PLW2901
            group,
            "asset",
        )

        percent_gain_benchmark = utils.calc_curr_perc_gain(
            group,
            "benchmark",
            sorting_columns=[{"columns": ["date"], "ascending": [False]}],
        )

        percent_gain_asset = utils.calc_curr_perc_gain(
            group,
            "asset",
            sorting_columns=[{"columns": ["date"], "ascending": [False]}],
        )

        assets_vs_benchmark.loc[len(assets_vs_benchmark)] = [
            group.iloc[0]["ticker_asset"],
            percent_gain_asset.iloc[0]["curr_perc_gain_asset"],
            percent_gain_benchmark.iloc[0]["curr_perc_gain_benchmark"],
        ]

    return assets_vs_benchmark


def _simulate_benchmark_absolute(
    benchmark: pd.DataFrame,
    portfolio_data: PortfolioData,
) -> pd.DataFrame:
    """Model the benchmark as if the same transaction value purchased of an asset of the portfolio
    was purchased of the benchmark (in absoulte value).

    :param benchmark: Benchmark historical data.
    :param portfolio_data: Transactions history and other portfolio data.
    :return: Dataframe with the simulated trans_qty_benchmark.
    """
    return benchmark.merge(
        portfolio_data.transactions[["date", "trans_qty_asset", "trans_val_asset"]],
        how="left",
        on=["date"],
    ).assign(
        trans_val_asset=lambda df: df["trans_val_asset"].fillna(0),
        trans_qty_asset=lambda df: df["trans_qty_asset"].fillna(0),
        trans_qty_benchmark=lambda df: -df["trans_val_asset"]
        / df["close_unadj_local_currency_benchmark"],
    )


def _simulate_benchmark_proportional(
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
            trans_qty_benchmark=np.float64(0.0),
        )
    )

    iterator = list(reversed(df.index))
    latest_curr_qty_benchmark = 0
    ever_purchased = False

    for i in iterator:
        # if first time purchasing
        if not ever_purchased and df.loc[i, "trans_qty_asset"] != 0:
            df.loc[i, "trans_qty_benchmark"] = (
                -df.loc[i, "trans_val_asset"] / df.loc[i, "close_unadj_local_currency_benchmark"]
            )
            latest_curr_qty_benchmark += df.loc[i, "trans_qty_benchmark"]
            ever_purchased = True

        # if purchasing for a second or more time
        elif df.loc[i, "trans_qty_asset"] != 0:
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
