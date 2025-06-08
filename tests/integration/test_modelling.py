"""Integration test for modelling."""

import pickle
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from stock_portfolio_tracker.entry_points._pipeline import _pipeline
from stock_portfolio_tracker.utils import DataApiType


def test_modelling() -> None:
    """Test the entire module package."""
    logger.info("Read artifacts.")

    pipeline_outputs = _pipeline(
        config_file_name="example_config.json",
        transactions_file_name="example_transactions.csv",
        data_api_type=DataApiType.TESTING,
        input_data_dir=Path("data/in/"),
        end_date=pd.Timestamp("31-12-2024"),
    )

    expected_outputs = _read_artifacts(
        file_path=Path("tests/integration/pipeline_output_artifacts"),
        file_name="pipeline_outputs.pkl",
    )

    assert all(
        pipeline_output.equals(expected_output)
        for pipeline_output, expected_output in zip(
            pipeline_outputs, expected_outputs, strict=False
        )
    ), "Pipeline outputs do not match expected outputs."


def _read_artifacts(file_path: Path, file_name: str) -> Any:
    """Read pickle file.

    Args:
        file_path: Path to the directory containing the artifacts.
        file_name: Name of the file containing the artifacts.

    Returns:
        Artifact object.
    """
    with Path.open(file_path / file_name, "rb") as file:
        return pickle.load(file)  # noqa: S301
