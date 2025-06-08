"""Main module to execute the project."""

import pickle
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from stock_portfolio_tracker import utils
from stock_portfolio_tracker.entry_points._pipeline import _pipeline
from stock_portfolio_tracker.preprocessing import Preprocessor
from stock_portfolio_tracker.preprocessing._interfaces import YahooFinanceApi
from stock_portfolio_tracker.utils import DataApiType

API_MOCKED_ARTIFACTS_PATH = Path("tests/integration/api_mocked_artifacts")
PIPELINE_OUTPUT_ARTIFACTS_PATH = Path("tests/integration/pipeline_output_artifacts")


def generate_api_mocked_artifacts(config_file_name: str, transactions_file_name: str) -> None:
    """Save API repsponses as pickles so they can be returned by the mocked testing API.

    Args:
        config_file_name: File name for config.
        transactions_file_name: File name for transactions.
    """
    logger.info("Deleting current artifacts.")
    utils.delete_current_artifacts(API_MOCKED_ARTIFACTS_PATH)

    logger.info("Start of preprocess.")
    preprocessor = Preprocessor(
        data_api_type=DataApiType.YAHOO_FINANCE.value,
        input_data_dir=Path("data/in/"),
        end_date=pd.Timestamp("31-12-2024"),
    )

    config = preprocessor._load_config(config_file_name=config_file_name)  # noqa: SLF001
    portfolio_data = preprocessor._load_portfolio_data(  # noqa: SLF001
        transactions_file_name=transactions_file_name
    )
    api_interface = YahooFinanceApi()
    start_date = portfolio_data.transactions["date"].min()

    for ticker in [
        *portfolio_data.transactions["ticker_asset"].unique().tolist(),
        config.benchmark_ticker,
    ]:
        logger.info(f"Saving data for ticker: {ticker}")
        artifact = api_interface.get_asset_historical_data(ticker=ticker, start_date=start_date)
        _save_pickle(
            path=API_MOCKED_ARTIFACTS_PATH,
            file_name=f"{ticker}_data",
            artifact=artifact[artifact["date"] <= preprocessor.end_date],
        )

    artifact = api_interface.get_currency_exchange_rate(
        origin_currency="USD", local_currency=config.portfolio_currency, start_date=start_date
    )
    _save_pickle(
        path=API_MOCKED_ARTIFACTS_PATH,
        file_name="currency_exchange_rate",
        artifact=artifact[artifact["date"] <= preprocessor.end_date],
    )


def generate_pipeline_output_artifacts(config_file_name: str, transactions_file_name: str) -> None:
    """Generate pipeline output artifacts based on the mocked testing API.

    Args:
        config_file_name: File name for config.
        transactions_file_name: File name for transactions.
    """
    artifacts = _pipeline(
        config_file_name=config_file_name,
        transactions_file_name=transactions_file_name,
        data_api_type=DataApiType.TESTING,
        input_data_dir=Path("data/in/"),
        end_date=pd.Timestamp("31-12-2024"),
    )

    logger.info("Deleting current artifacts.")
    utils.delete_current_artifacts(PIPELINE_OUTPUT_ARTIFACTS_PATH)

    _save_pickle(
        path=PIPELINE_OUTPUT_ARTIFACTS_PATH, file_name="pipeline_outputs", artifact=artifacts
    )


def _save_pickle(path: Path, file_name: str, artifact: Any) -> None:
    """Save artifact as pickle.

    Args:
        path: Path to the directory where the artifact will be saved.
        file_name: Name of the file to save the artifact as.
        artifact: The artifact to save.
    """
    with Path.open(path / Path(f"{file_name}.pkl"), "wb") as file:
        pickle.dump(artifact, file)


if __name__ == "__main__":
    generate_api_mocked_artifacts("example_config.json", "example_transactions.csv")
    generate_pipeline_output_artifacts("example_config.json", "example_transactions.csv")
