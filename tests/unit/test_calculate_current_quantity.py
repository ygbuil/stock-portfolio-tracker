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
            "asset_ticker": ["NVDA"] * 8,
            "close_unadjusted_local_currency": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "asset_split": [0, 0, 0, 0, 10, 0, 0, 0],
            "quantity": [np.nan, -1, 3, np.nan, np.nan, 3, 2, np.nan],
            "value": [np.nan, 100, -285, np.nan, np.nan, -3000, -2200, np.nan],
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
            ],
            "asset_ticker": ["NVDA"] * 8,
            "close_unadjusted_local_currency": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "asset_split": [0, 0, 0, 0, 10, 0, 0, 0],
            "quantity": [np.nan, -1, 3, np.nan, 4, 3, 2, np.nan],
            "value": [np.nan, 100, -285, np.nan, -360, -3000, -2200, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def current_quantity_1() -> pd.DataFrame:
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
            "asset_ticker": ["NVDA"] * 8,
            "close_unadjusted_local_currency": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "asset_split": [0, 0, 0, 0, 10, 0, 0, 0],
            "quantity": [np.nan, -1, 3, np.nan, np.nan, 3, 2, np.nan],
            "value": [np.nan, 100, -285, np.nan, np.nan, -3000, -2200, np.nan],
            "current_quantity": [52, 52, 53, 50, 50, 5, 2, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def current_quantity_2() -> pd.DataFrame:
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
            "asset_ticker": ["NVDA"] * 8,
            "close_unadjusted_local_currency": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "asset_split": [0, 0, 0, 0, 10, 0, 0, 0],
            "quantity": [np.nan, -1, 3, np.nan, 4, 3, 2, np.nan],
            "value": [np.nan, 100, -285, np.nan, -360, -3000, -2200, np.nan],
            "current_quantity": [56, 56, 57, 54, 54, 5, 2, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("transactions", "current_quantity"),
    [
        ("transactions_1", "current_quantity_1"),
        ("transactions_2", "current_quantity_2"),
    ],
)
def test_calculate_current_quantity(
    transactions: pd.DataFrame,
    current_quantity: pd.DataFrame,
    request: FixtureRequest,
) -> None:
    """Test calculate_current_quantity.

    :param transactions: Transactions.
    :param current_quantity: Resulting dataframe with the percent gain.
    :param request: FixtureRequest.
    """
    assert utils.calculate_current_quantity(
        request.getfixturevalue(transactions),
        "quantity",
    ).equals(request.getfixturevalue(current_quantity))
