"""Main module to execute the project."""

from pathlib import Path

import click
import pandas as pd
from loguru import logger

from stock_portfolio_tracker import modelling, reporting
from stock_portfolio_tracker.preprocessing import Preprocessor
from stock_portfolio_tracker.utils import DataApiType, timer


@click.command()
@click.option("--config-file-name")
@click.option("--transactions-file-name")
def execute_cli_pipeline(config_file_name: str, transactions_file_name: str) -> None:
    """Entry point for pipeline.

    Args:
        config_file_name: File name for config.
        transactions_file_name: File name for transactions.
    """
    pipeline(
        config_file_name=config_file_name,
        transactions_file_name=transactions_file_name,
    )


@timer
def pipeline(
    config_file_name: str,
    transactions_file_name: str,
    end_date: pd.Timestamp | None = None,
    data_api_type: DataApiType = DataApiType.YAHOO_FINANCE,
    input_data_dir: Path = Path("data/in/"),
) -> dict[str, pd.DataFrame]:
    """Execute the project end to end.

    Args:
        config_file_name: File name for config.
        transactions_file_name: File name for transactions.
        end_date: End date to use for the portfolio analysis.
        data_api_type: Type of data API to use.
        input_data_dir: Directory where input data files are located.
    """
    logger.info("Start of execution.")

    logger.info("Start of preprocess.")

    if not end_date:
        end_date = pd.Timestamp.today().normalize()

    config, portfolio_data, asset_prices, asset_dividends, benchmark_prices, benchmark_dividends = (
        Preprocessor(
            data_api_type=data_api_type.value, input_data_dir=input_data_dir, end_date=end_date
        ).preprocess(
            config_file_name,
            transactions_file_name,
        )
    )

    logger.info("Start of modelling.")
    (
        portfolio_evolution,
        benchmark_evolution,
        asset_distribution,
        assets_vs_benchmark,
        dividends_company,
        dividends_year,
        yearly_returns,
        overall_returns,
    ) = modelling.model_data(
        portfolio_data,
        asset_prices,
        asset_dividends,
        benchmark_prices,
    )

    logger.info("Start of generate reports.")
    reporting.generate_reports(
        config,
        portfolio_evolution,
        benchmark_evolution,
        asset_distribution,
        assets_vs_benchmark,
        dividends_company,
        dividends_year,
        yearly_returns,
        overall_returns,
    )

    logger.info("End of execution.")

    return {
        "portfolio_evolution": portfolio_evolution,
        "benchmark_evolution": benchmark_evolution,
        "asset_distribution": asset_distribution,
        "assets_vs_benchmark": assets_vs_benchmark,
        "dividends_company": dividends_company,
        "dividends_year": dividends_year,
        "yearly_returns": yearly_returns,
        "overall_returns": overall_returns,
    }
