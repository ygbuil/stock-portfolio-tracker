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
            "ticker_asset": ["NVDA"] * 8,
            "close_unadj_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "split_asset": [0, 0, 0, 0, 10, 0, 0, 0],
            "quantity_asset": [np.nan, -1, 3, np.nan, np.nan, 3, 2, np.nan],
            "value_asset": [np.nan, 100, -285, np.nan, np.nan, -3000, -2200, np.nan],
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
            "ticker_asset": ["NVDA"] * 8,
            "close_unadj_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "split_asset": [0, 0, 0, 0, 10, 0, 0, 0],
            "quantity_asset": [np.nan, -1, 3, np.nan, 4, 3, 2, np.nan],
            "value_asset": [np.nan, 100, -285, np.nan, -360, -3000, -2200, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def curr_qty_1() -> pd.DataFrame:
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
            "ticker_asset": ["NVDA"] * 8,
            "close_unadj_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "split_asset": [0, 0, 0, 0, 10, 0, 0, 0],
            "quantity_asset": [np.nan, -1, 3, np.nan, np.nan, 3, 2, np.nan],
            "value_asset": [np.nan, 100, -285, np.nan, np.nan, -3000, -2200, np.nan],
            "curr_qty_asset": [52, 52, 53, 50, 50, 5, 2, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def curr_qty_2() -> pd.DataFrame:
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
            "ticker_asset": ["NVDA"] * 8,
            "close_unadj_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "split_asset": [0, 0, 0, 0, 10, 0, 0, 0],
            "quantity_asset": [np.nan, -1, 3, np.nan, 4, 3, 2, np.nan],
            "value_asset": [np.nan, 100, -285, np.nan, -360, -3000, -2200, np.nan],
            "curr_qty_asset": [56, 56, 57, 54, 54, 5, 2, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("transactions", "curr_qty"),
    [
        ("transactions_1", "curr_qty_1"),
        ("transactions_2", "curr_qty_2"),
    ],
)
def test_calculate_curr_qty(
    transactions: pd.DataFrame,
    curr_qty: pd.DataFrame,
    request: FixtureRequest,
) -> None:
    """Test calculate_curr_qty.

    :param transactions: Transactions.
    :param curr_qty: Resulting dataframe with the percent gain.
    :param request: FixtureRequest.
    """
    assert utils.calculate_curr_qty(
        request.getfixturevalue(transactions),
        "quantity_asset",
        "asset",
    ).equals(request.getfixturevalue(curr_qty))
