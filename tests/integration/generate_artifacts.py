"""Main module to execute the project."""

import pickle
from pathlib import Path

from loguru import logger

from stock_portfolio_tracker import modelling, preprocessing

ARTIFACTS_PATH = Path("tests/integration/artifacts")


def generate_artifacts(config_file_name: str, transactions_file_name: str) -> None:
    """Generate static preprocess and model_data outputs so that an snapshot of known successful
    input outpus can be saved for integration testing.

    :param config_file_name: File name for config.
    :param transactions_file_name: File name for transactions.
    """
    logger.info("Start of execution.")
    _delete_current_artifacts(ARTIFACTS_PATH)

    logger.info("Start of preprocess.")
    config, portfolio_data, asset_prices, asset_dividends, benchmark_prices, benchmark_dividends = (
        preprocessing.preprocess(
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
        assets_distribution,
        benchmark_val_evolution_abs,
        assets_vs_benchmark,
        benchmark_gain_evolution,
        dividends_company,
        dividends_year,
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
            "assets_distribution": assets_distribution,
            "benchmark_val_evolution_abs": benchmark_val_evolution_abs,
            "assets_vs_benchmark": assets_vs_benchmark,
            "benchmark_gain_evolution": benchmark_gain_evolution,
            "dividends_company": dividends_company,
            "dividends_year": dividends_year,
        },
    )

    logger.info("End of execution.")


def _delete_current_artifacts(directory: Path) -> None:
    """Delete all artifacts in the specified directory except for `.gitkeep` files.

    :param directory: The path to the directory where files should be deleted.
    """
    logger.info("Deleting existing artifacts.")
    for file_path in directory.iterdir():
        if file_path.name != ".gitkeep" and file_path.is_file():
            file_path.unlink()
            logger.info(f"Deleted: {file_path}")


def _save_artifacts(artifacts: dict) -> None:
    """Save artifacts.

    :param artifacts: Dictionary containing key=<artifact_file_name> and value=<artifact_objetc>.
    """
    for file_name, artifact in artifacts.items():
        with Path.open(ARTIFACTS_PATH / Path(f"{file_name}.pkl"), "wb") as file:
            pickle.dump(artifact, file)


if __name__ == "__main__":
    generate_artifacts("example_config.json", "example_transactions.csv")
