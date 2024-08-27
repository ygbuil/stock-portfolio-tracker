import pandas as pd

from stock_portfolio_tracker.objetcs import PortfolioData

from . import _utils as utils


def model_benchmarks_absolute(
    portfolio_data: PortfolioData, benchmarks: pd.DataFrame
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
        "benchmark"
    )

    benchmark_value_evolution_absolute = utils.calculate_current_value(
        benchmark_value_evolution_absolute,
        "benchmark",
    ).assign(current_value_benchmark=lambda df: round(df["current_value_benchmark"], 2))

    benchmark_percent_evolution = utils.calculate_current_percent_gain(
        pd.merge(
            benchmark_value_evolution_absolute[["date", "ticker_benchmark", "current_value_benchmark"]],
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
    portfolio_model: pd.DataFrame, benchmarks: pd.DataFrame
) -> pd.DataFrame:
    groups = []

    for _, group in portfolio_model.groupby("ticker_asset"):
        group = pd.merge(
            benchmarks[["date", "ticker_asset", "split_asset", "close_unadjusted_local_currency"]],
            group[["date", "ticker_asset", "quantity", "current_quantity", "close_unadjusted_local_currency", "value"]],
            "left",
            on=["date"],
        ).rename(
            columns={"ticker_asset_x": "ticker_asset_benchmark", 
                     "close_unadjusted_local_currency_x": "close_unadjusted_local_currency_benchmark", 
                     "ticker_asset_y": "ticker_asset",
                     "close_unadjusted_local_currency_y": "close_unadjusted_local_currency_asset"}
        )

        group = utils.calculate_benchmark_quantity(group)

        group = utils.calculate_current_quantity(
            group.drop("current_quantity", axis=1),
            "benchmark_quantity",
        )

        group = utils.calculate_current_value(
            group,
            "benchmark_value",
        ).assign(benchmark_value=lambda df: round(df["benchmark_value"], 2))

        group = utils.calculate_current_percent_gain(
            group,
            "benchmark_value",
        )

        groups.append(group)

    groups = utils.sort_by_columns(
        pd.concat(groups),
        ["ticker_asset", "date"],
        [True, False],
    )

    benchmark_value_evolution_proportional = utils.calculate_current_value(
        groups,
        "benchmark_value",
    ).assign(benchmark_value=lambda df: round(df["benchmark_value"], 2))

    return benchmark_value_evolution_proportional, groups
