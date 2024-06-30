"""Modelling unit tests."""

import numpy as np
import pandas as pd
import pytest
from pytest import FixtureRequest  # noqa: PT013

import stock_portfolio_tracker.modelling._utils as utils


@pytest.fixture()
def transactions_1() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-07",
                "2024-01-06",
                "2024-01-06",
                "2024-01-05",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
            ],
            "value": [-100, 130, 600, np.nan, np.nan, 120, np.nan, -1000],
            "current_portfolio_value": [1150, 1000, 950, 1500, 1080, 1210, 1200, 1100],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def transactions_2() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-07",
                "2024-01-06",
                "2024-01-06",
                "2024-01-05",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
                "2023-12-31",
            ],
            "value": [-100, 130, 600, np.nan, np.nan, 120, np.nan, -1000, np.nan],
            "current_portfolio_value": [1150, 1000, 950, 1500, 1080, 1210, 1200, 1100, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def current_percent_gain_1() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-07",
                "2024-01-06",
                "2024-01-05",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
            ],
            "current_gain": [900.0, 850.0, 620.0, 200.0, 330.0, 200.0, 0.0],
            "current_percent_gain": [81.82, 85.0, 62.0, 20.0, 33.0, 20.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def current_percent_gain_2() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-07",
                "2024-01-06",
                "2024-01-05",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
                "2023-12-31",
            ],
            "current_gain": [900.0, 850.0, 620.0, 200.0, 330.0, 200.0, 100, 0],
            "current_percent_gain": [81.82, 85.0, 62.0, 20.0, 33.0, 20.0, 10.0, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("transactions", "current_percent_gain"),
    [
        ("transactions_1", "current_percent_gain_1"),
        ("transactions_2", "current_percent_gain_2"),
    ],
)
def test_calculate_current_percent_gain(
    transactions: pd.DataFrame,
    current_percent_gain: pd.DataFrame,
    request: FixtureRequest,
) -> None:
    """Test calculate_current_percent_gain.

    :param transactions: Transactions.
    :param current_percent_gain: Resulting dataframe with the percent gain.
    :param request: FixtureRequest.
    """
    assert utils.calculate_current_percent_gain(
        request.getfixturevalue(transactions),
        "current_portfolio_value",
    ).equals(request.getfixturevalue(current_percent_gain))
