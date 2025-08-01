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

    Args:
        portfolio_data: Transactions history and other portfolio data.
        asset_prices: Benchmark historical data.
        asset_dividends: Asset prices historical data.
        benchmark_prices: Dataframe containing the dividend amount on the Ex-Dividend Date.

    Returns:
        Relevant modelled data.
    """
    logger.info("Modelling portfolio.")
    (
        portfolio_evolution,
        asset_distribution,
        portfolio_model,
        dividends_company,
        dividends_year,
        portfolio_returns,
    ) = modelling_portfolio.model_portfolio(
        portfolio_data,
        asset_prices,
        asset_dividends,
        sorting_columns=[
            {"columns": ["date"], "ascending": [False]},
            {"columns": ["curr_val_asset"], "ascending": [False]},
            {"columns": ["ticker_asset", "date"], "ascending": [True, False]},
            {"columns": ["total_dividend_asset"], "ascending": [True]},
            {"columns": ["date"], "ascending": [True]},
            {"columns": ["metric_type", "unit_type", "year"], "ascending": [True, True, False]},
        ],
    )

    logger.info("Modelling benchmark.")
    benchmark_evolution, benchmark_returns = modelling_benchmark.model_benchmark(
        portfolio_data,
        benchmark_prices,
        sorting_columns=[
            {"columns": ["date"], "ascending": [False]},
            {"columns": ["metric_type", "unit_type", "year"], "ascending": [True, True, False]},
        ],
    )

    logger.info("Modelling assets vs benchmark.")
    assets_vs_benchmark = modelling_benchmark.model_assets_vs_benchmark(
        portfolio_model,
        benchmark_prices,
        sorting_columns=[{"columns": ["diff"], "ascending": [False]}],
    ).drop(columns=["diff"])

    logger.info("End of modelling.")

    return (
        portfolio_evolution.merge(benchmark_evolution, on="date", how="left").assign(
            curr_val_diff=lambda df: df["curr_val_portfolio"] - df["curr_val_benchmark"],
            curr_abs_gain_diff=lambda df: df["curr_abs_gain_portfolio"]
            - df["curr_abs_gain_benchmark"],
            curr_perc_gain_diff=lambda df: df["curr_perc_gain_portfolio"]
            - df["curr_perc_gain_benchmark"],
        ),
        asset_distribution,
        assets_vs_benchmark,
        dividends_company,
        dividends_year,
        portfolio_returns.merge(
            benchmark_returns, how="left", on=["metric_type", "unit_type", "year"]
        ),
    )
