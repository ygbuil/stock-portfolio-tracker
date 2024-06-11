import pandas as pd
from objetcs import PortfolioData

from . import _utils as utils


def model_benchmarks(portfolio_data: PortfolioData, benchmarks: pd.DataFrame) -> pd.DataFrame:
    benchmark_value_evolution = pd.merge(
        benchmarks,
        portfolio_data.transactions[["date", "quantity", "value"]],
        "left",
        on=["date"],
    )
    benchmark_value_evolution["benchmark_quantity"] = (
        -benchmark_value_evolution["value"]
        / benchmark_value_evolution["open_unadjusted_local_currency"]
    )
    benchmark_value_evolution = utils.calculate_current_quantity(
        benchmark_value_evolution,
        "benchmark_quantity",
    )

    benchmark_value_evolution = utils.calculate_current_value(
        benchmark_value_evolution,
        "benchmark_value",
    )

    return utils.sort_by_ticker_date(
        benchmark_value_evolution,
        ["asset_ticker", "date"],
        [True, False],
    )
