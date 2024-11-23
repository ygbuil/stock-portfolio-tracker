"""Calculate all necessary metrics."""

import pandas as pd
from loguru import logger

from stock_portfolio_tracker.utils import PortfolioData

from . import _modelling_benchmark as modelling_benchmark
from . import _modelling_portfolio as modelling_portfolio


def model_data(
    portfolio_data: PortfolioData,
    asset_prices: pd.DataFrame,
    asset_dividends: pd.DataFrame,
    benchmark_prices: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """Calculate all necessary metrics.

    :param portfolio_data: Transactions history and other portfolio data.
    :param benchmark_prices: Benchmark historical data.
    :param asset_prices: Asset prices historical data.
    :param asset_dividends: Dataframe containing the dividend amount on the Ex-Dividend Date.
    :return: Relevant modelled data.
    """
    logger.info("Modelling portfolio.")
    (
        portfolio_evolution,
        asset_distribution,
        portfolio_model,
        dividends_company,
        dividends_year,
    ) = modelling_portfolio.model_portfolio(
        portfolio_data,
        asset_prices,
        asset_dividends,
        sorting_columns=[
            {"columns": ["date"], "ascending": [False]},
            {"columns": ["curr_val_asset"], "ascending": [False]},
            {"columns": ["ticker_asset", "date"], "ascending": [True, False]},
            {"columns": ["total_dividend_asset"], "ascending": [False]},
            {"columns": ["date"], "ascending": [True]},
        ],
    )

    logger.info("Modelling benchmark absolute.")
    benchmark_evolution = modelling_benchmark.model_benchmark_absolute(
        portfolio_data,
        benchmark_prices,
        sorting_columns=[
            {"columns": ["date"], "ascending": [False]},
            {"columns": ["date"], "ascending": [False]},
        ],
    )

    logger.info("Modelling benchmark proportional.")
    assets_vs_benchmark = modelling_benchmark.model_benchmark_proportional(
        portfolio_model,
        benchmark_prices,
        sorting_columns=[{"columns": ["curr_perc_gain_asset"], "ascending": [False]}],
    )

    logger.info("End of modelling.")

    return (
        portfolio_evolution,
        benchmark_evolution,
        asset_distribution,
        assets_vs_benchmark,
        dividends_company,
        dividends_year,
    )
