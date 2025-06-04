"""Main module to execute the project."""

import pickle
from pathlib import Path
from typing import Any

from loguru import logger

from stock_portfolio_tracker import modelling, utils
from stock_portfolio_tracker.preprocessing import Preprocessor
from stock_portfolio_tracker.utils import DataApiType

ARTIFACTS_PATH = Path("tests/integration/artifacts")


def generate_artifacts(config_file_name: str, transactions_file_name: str) -> None:
    """Generate static preprocess and model_data outputs so that an snapshot of known successful
    input outpus can be saved for integration testing.

    Args:
        config_file_name: File name for config.
        transactions_file_name: File name for transactions.
    """
    logger.info("Start of execution.")
    utils.delete_current_artifacts(ARTIFACTS_PATH)

    logger.info("Start of preprocess.")
    config, portfolio_data, asset_prices, asset_dividends, benchmark_prices, benchmark_dividends = (
        Preprocessor(data_api_type=DataApiType.YAHOO_FINANCE.value).preprocess(
            config_file_name,
            transactions_file_name,
        )
    )

    logger.info("Saving pickle inputs.")
    _save_artifacts(
        {
            "config": config,
            "portfolio_data": portfolio_data,
            "asset_prices": asset_prices,
            "asset_dividends": asset_dividends,
            "benchmark_prices": benchmark_prices,
        },
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

    logger.info("Saving pickle outputs.")
    _save_artifacts(
        {
            "portfolio_evolution": portfolio_evolution,
            "benchmark_evolution": benchmark_evolution,
            "asset_distribution": asset_distribution,
            "assets_vs_benchmark": assets_vs_benchmark,
            "dividends_company": dividends_company,
            "dividends_year": dividends_year,
            "yearly_returns": yearly_returns,
            "overall_returns": overall_returns,
        },
    )

    logger.info("End of execution.")


def _save_artifacts(artifacts: dict[str, Any]) -> None:
    """Save artifacts.

    Args:
        artifacts: Dictionary containing key=<artifact_file_name> and value=<artifact_objetc>.
    """
    for file_name, artifact in artifacts.items():
        with Path.open(ARTIFACTS_PATH / Path(f"{file_name}.pkl"), "wb") as file:
            pickle.dump(artifact, file)


if __name__ == "__main__":
    generate_artifacts("example_config.json", "example_transactions.csv")
