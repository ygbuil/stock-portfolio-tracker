import pandas as pd

from stock_portfolio_tracker.utils import PortfolioData, sort_at_end

from . import _utils as utils


@sort_at_end()
def model_benchmarks_absolute(
    portfolio_data: PortfolioData,
    benchmarks: pd.DataFrame,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
    benchmark_value_evolution_absolute = benchmarks.merge(
        portfolio_data.transactions[["date", "quantity_asset", "value_asset"]],
        how="left",
        on=["date"],
    ).assign(
        quantity_benchmark=lambda df: -df["value_asset"]
        / df["close_unadjusted_local_currency_benchmark"],
    )

    benchmark_value_evolution_absolute = utils.calculate_current_quantity(
        benchmark_value_evolution_absolute,
        "quantity_benchmark",
        "benchmark",
    )

    benchmark_value_evolution_absolute = utils.calculate_current_value(
        benchmark_value_evolution_absolute,
        "benchmark",
    ).assign(current_value_benchmark=lambda df: round(df["current_value_benchmark"], 2))

    benchmark_percent_evolution = utils.calculate_current_percent_gain(
        benchmark_value_evolution_absolute[["date", "ticker_benchmark", "current_value_benchmark"]]
        .merge(
            portfolio_data.transactions[["date", "value_asset"]],
            how="left",
            on=["date"],
        )
        .rename(columns={"value_asset": "value_benchmark"}),
        "benchmark",
        "current_value_benchmark",
        sorting_columns=[{"columns": ["date"], "ascending": [False]}],
    )

    return benchmark_value_evolution_absolute, benchmark_percent_evolution


@sort_at_end()
def model_benchmarks_proportional(
    portfolio_model: pd.DataFrame,
    benchmarks: pd.DataFrame,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
    individual_assets_vs_benchmark_returns = pd.DataFrame(
        {
            "ticker_asset": [],
            "current_percent_gain_asset": [],
            "current_percent_gain_benchmark": [],
        },
    )

    for _, group in portfolio_model.groupby("ticker_asset"):
        group = benchmarks[  # noqa: PLW2901
            [
                "date",
                "ticker_benchmark",
                "split_benchmark",
                "close_unadjusted_local_currency_benchmark",
            ]
        ].merge(
            group[
                [
                    "date",
                    "ticker_asset",
                    "quantity_asset",
                    "current_quantity_asset",
                    "close_unadjusted_local_currency_asset",
                    "value_asset",
                ]
            ],
            how="left",
            on=["date"],
        )

        group = utils.calculate_quantity_benchmark(group)  # noqa: PLW2901

        group = utils.calculate_current_quantity(  # noqa: PLW2901
            group,
            "quantity_benchmark",
            "benchmark",
        )

        group = utils.calculate_current_value(  # noqa: PLW2901
            group,
            "benchmark",
        )

        group = utils.calculate_current_value(  # noqa: PLW2901
            group,
            "asset",
        )

        percent_gain_benchmark = utils.calculate_current_percent_gain(
            group,
            "benchmark",
            "current_value_benchmark",
            sorting_columns=[{"columns": ["date"], "ascending": [False]}],
        )

        percent_gain_asset = utils.calculate_current_percent_gain(
            group,
            "asset",
            "current_value_asset",
            sorting_columns=[{"columns": ["date"], "ascending": [False]}],
        )

        individual_assets_vs_benchmark_returns.loc[len(individual_assets_vs_benchmark_returns)] = [
            group.iloc[0]["ticker_asset"],
            percent_gain_asset.iloc[0]["current_percent_gain_asset"],
            percent_gain_benchmark.iloc[0]["current_percent_gain_benchmark"],
        ]

    return individual_assets_vs_benchmark_returns
