"""Calculate all necessary metrics."""

import pandas as pd
from loguru import logger

from stock_portfolio_tracker.utils import PortfolioData

from . import _modelling_benchmark as modelling_benchmark
from . import _modelling_portfolio as modelling_portfolio


def model_data(
    portfolio_data: PortfolioData,
    benchmark: pd.DataFrame,
    asset_prices: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Calculate all necessary metrics.

    :param portfolio_data: Transactions history and other portfolio data.
    :param benchmark: Benchmark historical data.
    :param asset_prices: Asset prices historical data.
    :return: Relevant modelled data.
    """
    logger.info("Modelling portfolio.")
    (
        portfolio_evolution,
        assets_distribution,
        portfolio_model,
    ) = modelling_portfolio.model_portfolio(
        portfolio_data,
        asset_prices,
        sorting_columns=[
            {"columns": ["date"], "ascending": [False]},
            {"columns": ["date"], "ascending": [False]},
            {"columns": ["curr_val_asset"], "ascending": [False]},
            {"columns": ["ticker_asset", "date"], "ascending": [True, False]},
        ],
    )

    logger.info("Modelling benchmark absolute.")
    benchmark_val_evolution_abs, benchmark_perc_evolution = (
        modelling_benchmark.model_benchmark_absolute(
            portfolio_data,
            benchmark,
            sorting_columns=[
                {"columns": ["date"], "ascending": [False]},
                {"columns": ["date"], "ascending": [False]},
            ],
        )
    )

    logger.info("Modelling benchmark proportional.")
    assets_vs_benchmark = modelling_benchmark.model_benchmark_proportional(
        portfolio_model,
        benchmark,
        sorting_columns=[{"columns": ["curr_perc_gain_asset"], "ascending": [False]}],
    )

    logger.info("End of modelling.")

    return (
        portfolio_evolution,
        assets_distribution,
        benchmark_val_evolution_abs,
        assets_vs_benchmark,
        benchmark_perc_evolution,
    )
