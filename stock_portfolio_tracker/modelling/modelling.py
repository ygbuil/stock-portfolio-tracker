"""Calculate all necessary metrics."""

import pandas as pd
from loguru import logger

from stock_portfolio_tracker.objetcs import PortfolioData

from . import _modelling_benchmark as modelling_benchmark
from . import _modelling_portfolio as modelling_portfolio


def model_data(
    portfolio_data: PortfolioData,
    benchmarks: pd.DataFrame,
    asset_prices: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Calculate all necessary metrics.

    :param portfolio_data: All data of user's portfolio.
    :param benchmarks: Benchmark historical data.
    :param asset_prices: Asset prices historical data.
    :return: Relevant modelled data.
    """
    logger.info("Start of modelling.")

    logger.info("Modelling portfolio.")
    (
        asset_portfolio_value_evolution,
        asset_portfolio_percent_evolution,
        asset_portfolio_current_positions,
        portfolio_model,
    ) = modelling_portfolio.model_portfolio(
        portfolio_data,
        asset_prices,
        sorting_columns=[
            {"columns": ["date"], "ascending": [False]},
            {"columns": ["date"], "ascending": [False]},
            {"columns": ["current_position_value"], "ascending": [False]},
            {"columns": ["ticker_asset", "date"], "ascending": [True, False]},
        ],
    )

    logger.info("Modelling benchmark.")
    benchmark_value_evolution_absolute, benchmark_percent_evolution = (
        modelling_benchmark.model_benchmarks_absolute(
            portfolio_data,
            benchmarks,
            sorting_columns=[
                {"columns": ["ticker_benchmark", "date"], "ascending": [True, False]},
                {"columns": ["date"], "ascending": [False]},
            ],
        )
    )
    individual_assets_vs_benchmark_returns = modelling_benchmark.model_benchmarks_proportional(
        portfolio_model,
        benchmarks,
        sorting_columns=[{"columns": ["current_percent_gain_asset"], "ascending": [False]}],
    )

    logger.info("End of modelling.")

    return (
        asset_portfolio_value_evolution,
        asset_portfolio_percent_evolution,
        asset_portfolio_current_positions,
        benchmark_value_evolution_absolute,
        individual_assets_vs_benchmark_returns,
        benchmark_percent_evolution,
    )
