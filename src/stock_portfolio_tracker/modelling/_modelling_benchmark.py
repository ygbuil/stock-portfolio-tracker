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
    benchmark_val_evolution_abs = benchmark.merge(
        portfolio_data.transactions[["date", "trans_qty_asset", "trans_val_asset"]],
        how="left",
        on=["date"],
    ).assign(
        trans_qty_benchmark=lambda df: -df["trans_val_asset"]
        / df["close_unadj_local_currency_benchmark"],
    )

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

        group = utils.simulate_benchmark_proportional(group)  # noqa: PLW2901

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
