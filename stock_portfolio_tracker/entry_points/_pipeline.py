"""Main module to execute the project."""

import click
from loguru import logger

from stock_portfolio_tracker import modelling, preprocessing, reporting
from stock_portfolio_tracker.utils import timer


@click.command()
def pipeline() -> None:
    """Entry point for pipeline."""
    _pipeline()


@timer
def _pipeline() -> None:
    """Execute the project end to end."""
    logger.info("Start of execution.")

    logger.info("Start of preprocess.")
    config, portfolio_data, asset_prices, benchmarks = preprocessing.preprocess()

    logger.info("Start of modelling.")
    (
        asset_portfolio_value_evolution,
        asset_portfolio_percent_evolution,
        asset_distribution,
        benchmark_value_evolution_absolute,
        individual_assets_vs_benchmark_returns,
        benchmark_percent_evolution,
    ) = modelling.model_data(
        portfolio_data,
        benchmarks,
        asset_prices,
    )

    logger.info("Start of generate reports.")
    reporting.generate_reports(
        config,
        asset_portfolio_value_evolution,
        asset_portfolio_percent_evolution,
        asset_distribution,
        benchmark_value_evolution_absolute,
        individual_assets_vs_benchmark_returns,
        benchmark_percent_evolution,
    )

    logger.info("End of execution.")
