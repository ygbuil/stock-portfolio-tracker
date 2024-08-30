import pandas as pd

from stock_portfolio_tracker.objetcs import PortfolioData

from . import _utils as utils


def model_benchmarks_absolute(
    portfolio_data: PortfolioData,
    benchmarks: pd.DataFrame,
) -> pd.DataFrame:
    benchmark_value_evolution_absolute = pd.merge(
        benchmarks,
        portfolio_data.transactions[["date", "quantity_asset", "value_asset"]],
        "left",
        on=["date"],
    ).assign(
        quantity_benchmark=lambda df: df.apply(
            lambda x: -x["value_asset"] / x["close_unadjusted_local_currency_benchmark"],
            axis=1,
        ),
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
        pd.merge(
            benchmark_value_evolution_absolute[
                ["date", "ticker_benchmark", "current_value_benchmark"]
            ],
            portfolio_data.transactions[["date", "value_asset"]],
            "left",
            on=["date"],
        ).rename(columns={"value_asset": "value_benchmark"}),
        "benchmark",
        "current_value_benchmark",
    )

    return utils.sort_by_columns(
        benchmark_value_evolution_absolute,
        ["ticker_benchmark", "date"],
        [True, False],
    ), utils.sort_by_columns(
        benchmark_percent_evolution,
        ["date"],
        [False],
    )


def model_benchmarks_proportional(
    portfolio_model: pd.DataFrame,
    benchmarks: pd.DataFrame,
) -> pd.DataFrame:
    individual_assets_vs_benchmark_returns = pd.DataFrame(
        {
            "ticker_asset": [],
            "current_percent_gain_asset": [],
            "current_percent_gain_benchmark": [],
        },
    )

    for _, group in portfolio_model.groupby("ticker_asset"):
        group = pd.merge(  # noqa: PLW2901
            benchmarks[
                [
                    "date",
                    "ticker_benchmark",
                    "split_benchmark",
                    "close_unadjusted_local_currency_benchmark",
                ]
            ],
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
            "left",
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
        )

        percent_gain_asset = utils.calculate_current_percent_gain(
            group,
            "asset",
            "current_value_asset",
        )

        individual_assets_vs_benchmark_returns.loc[len(individual_assets_vs_benchmark_returns)] = [
            group.iloc[0]["ticker_asset"],
            utils.sort_by_columns(
                percent_gain_asset,
                ["date"],
                [False],
            ).iloc[0]["current_percent_gain_asset"],
            utils.sort_by_columns(
                percent_gain_benchmark,
                ["date"],
                [False],
            ).iloc[0]["current_percent_gain_benchmark"],
        ]

    return utils.sort_by_columns(
        individual_assets_vs_benchmark_returns,
        ["current_percent_gain_asset"],
        [False],
    )
