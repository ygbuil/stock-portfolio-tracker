"""Calculate all necessary metrics."""

import pandas as pd
from loguru import logger
from objetcs import PortfolioData

from . import _modelling_benchmark as modelling_benchmark
from . import _modelling_portfolio as modelling_portfolio


def model_data(
    portfolio_data: PortfolioData,
    benchmarks: pd.DataFrame,
    stock_prices: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Calculate all necessary metrics.

    :param portfolio_data: All data of user's portfolio.
    :param benchmarks: Benchmark historical data.
    :param stock_prices: Stock prices historical data.
    :return: Relevant modelled data.
    """
    logger.info("Start of modelling.")

    logger.info("Modelling portfolio.")
    stock_portfolio_value_evolution, stock_portfolio_current_positions = (
        modelling_portfolio.model_portfolio(
            portfolio_data,
            stock_prices,
        )
    )

    logger.info("Modelling benchmark.")
    benchmark_value_evolution = modelling_benchmark.model_benchmarks(portfolio_data, benchmarks)

    logger.info("End of modelling.")

    return (
        stock_portfolio_value_evolution,
        stock_portfolio_current_positions,
        benchmark_value_evolution,
    )
