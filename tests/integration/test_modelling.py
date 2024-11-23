"""Integration test for modelling."""

import pickle
from pathlib import Path

from loguru import logger

from stock_portfolio_tracker import modelling

ARTIFACTS_PATH = Path("tests/integration/artifacts")


def test_modelling() -> None:
    """Test the entire module package."""
    logger.info("Read artifacts.")

    config, portfolio_data, asset_prices, asset_dividends, benchmark_prices = _read_artifacts(
        ["config", "portfolio_data", "asset_prices", "asset_dividends", "benchmark_prices"],
    )

    logger.info("Start of modelling.")
    outputs = modelling.model_data(
        portfolio_data,
        asset_prices,
        asset_dividends,
        benchmark_prices,
    )

    expected_outputs = _read_artifacts(
        [
            "portfolio_evolution",
            "benchmark_evolution",
            "asset_distribution",
            "assets_vs_benchmark",
            "dividends_company",
            "dividends_year",
        ],
    )

    assert all(
        output.equals(expected_output)
        for output, expected_output in zip(outputs, expected_outputs, strict=False)
    )


def _read_artifacts(artifact_names: list[str]) -> list:
    artifacts_loaded = []

    for artifact_name in artifact_names:
        with Path.open(ARTIFACTS_PATH / Path(f"{artifact_name}.pkl"), "rb") as file:
            artifacts_loaded.append(pickle.load(file))  # noqa: S301

    return artifacts_loaded
