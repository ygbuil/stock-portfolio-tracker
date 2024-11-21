"""Modelling unit tests."""

import pandas as pd
import pytest
from pytest import FixtureRequest  # noqa: PT013

import stock_portfolio_tracker.modelling._utils as utils


@pytest.fixture
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
            "split_asset": [1, 1, 1, 1, 10, 1, 1, 1],
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "trans_val_asset": [0, 100, -285, 0, 0, -3000, -2200, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
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
            "split_asset": [1, 1, 1, 1, 10, 1, 1, 1],
            "trans_qty_asset": [0, -1, 3, 0, 4, 3, 2, 0],
            "trans_val_asset": [0, 100, -285, 0, -360, -3000, -2200, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
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
            "split_asset": [1, 1, 1, 1, 10, 1, 1, 1],
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "trans_val_asset": [0, 100, -285, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [52, 52, 53, 50, 50, 5, 2, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
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
            "split_asset": [1, 1, 1, 1, 10, 1, 1, 1],
            "trans_qty_asset": [0, -1, 3, 0, 4, 3, 2, 0],
            "trans_val_asset": [0, 100, -285, 0, -360, -3000, -2200, 0],
            "curr_qty_asset": [56.0, 56.0, 57.0, 54.0, 54.0, 5.0, 2.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("transactions", "curr_qty"),
    [
        ("transactions_1", "curr_qty_1"),
        ("transactions_2", "curr_qty_2"),
    ],
)
def test_calc_curr_qty(
    transactions: str,
    curr_qty: str,
    request: FixtureRequest,
) -> None:
    """Test calc_curr_qty.

    :param transactions: Transactions.
    :param curr_qty: Resulting dataframe with the percent gain.
    :param request: FixtureRequest.
    """
    assert utils.calc_curr_qty(
        request.getfixturevalue(transactions),
        "asset",
    ).equals(request.getfixturevalue(curr_qty))
