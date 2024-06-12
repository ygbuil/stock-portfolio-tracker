import pandas as pd
from objetcs import PortfolioData

from . import _utils as utils


def model_benchmarks(portfolio_data: PortfolioData, benchmarks: pd.DataFrame) -> pd.DataFrame:
    benchmark_value_evolution = pd.merge(
        benchmarks,
        portfolio_data.transactions[["date", "quantity", "value"]],
        "left",
        on=["date"],
    ).assign(
        benchmark_quantity=lambda df: df.apply(
            lambda x: -x["value"] / x["close_unadjusted_local_currency"],
            axis=1,
        ),
    )

    benchmark_value_evolution = utils.calculate_current_quantity(
        benchmark_value_evolution,
        "benchmark_quantity",
    )

    benchmark_value_evolution = utils.calculate_current_value(
        benchmark_value_evolution,
        "benchmark_value",
    ).assign(benchmark_value=lambda df: round(df["benchmark_value"], 2))

    benchmark_percent_evolution = utils.calculate_current_percent_gain(
        pd.merge(
            benchmark_value_evolution[["date", "asset_ticker", "benchmark_value"]],
            portfolio_data.transactions[["date", "value"]],
            "left",
            on=["date"],
        ),
        "benchmark_value",
    )

    return utils.sort_by_columns(
        benchmark_value_evolution,
        ["asset_ticker", "date"],
        [True, False],
    ), utils.sort_by_columns(
        benchmark_percent_evolution,
        ["date"],
        [False],
    )
