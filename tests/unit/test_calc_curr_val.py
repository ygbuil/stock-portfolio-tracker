"""Test calc_curr_val()."""

import pandas as pd
import pytest
from pytest import FixtureRequest  # noqa: PT013

import stock_portfolio_tracker.modelling._utils as utils


@pytest.fixture
def portfolio_model_1() -> pd.DataFrame:
    """Test calculate current value without transaction on split day and multiple transactions a
    day.

    Returns:
        Portfolio model.
    """
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
            "split_asset": [1, 1, 1, 1, 10, 1, 1, 1],
            "close_unadj_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "trans_val_asset": [0, 100, -285, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [52, 52, 53, 50, 50, 5, 2, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def portfolio_model_2() -> pd.DataFrame:
    """Test calculate current value with transaction on split day and multiple transactions a day.

    Returns:
        Portfolio model.
    """
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
            "split_asset": [1, 1, 1, 1, 10, 1, 1, 1],
            "close_unadj_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "trans_qty_asset": [0, -1, 3, 0, 4, 3, 2, 0],
            "trans_val_asset": [0, 100, -285, 0, -360, -3000, -2200, 0],
            "curr_qty_asset": [56, 56, 57, 54, 54, 5, 2, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def curr_val_1() -> pd.DataFrame:
    """Test calculate current value with transaction on split day and multiple transactions a day.

    Returns:
        Dataframe with current value.
    """
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
            "split_asset": [1, 1, 1, 1, 10, 1, 1, 1],
            "close_unadj_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "trans_val_asset": [0, 100, -285, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [52, 52, 53, 50, 50, 5, 2, 0],
            "curr_val_asset": [5720, 5200, 5035, 5000, 4500, 5000, 2200, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def curr_val_2() -> pd.DataFrame:
    """Test calculate current value without transaction on split day and multiple transactions a
    day.

    Returns:
        Dataframe with current value.
    """
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
            "split_asset": [1, 1, 1, 1, 10, 1, 1, 1],
            "close_unadj_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "trans_qty_asset": [0, -1, 3, 0, 4, 3, 2, 0],
            "trans_val_asset": [0, 100, -285, 0, -360, -3000, -2200, 0],
            "curr_qty_asset": [56, 56, 57, 54, 54, 5, 2, 0],
            "curr_val_asset": [6160, 5600, 5415, 5400, 4860, 5000, 2200, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("portfolio_model", "curr_val"),
    [
        ("portfolio_model_1", "curr_val_1"),
        ("portfolio_model_2", "curr_val_2"),
    ],
)
def test_calc_curr_val(
    portfolio_model: str,
    curr_val: str,
    request: FixtureRequest,
) -> None:
    """Test calc_curr_val.

    Args:
        portfolio_model: Input dataframe.
        curr_val: Output dataframe.
        request: FixtureRequest.
    """
    assert utils.calc_curr_val(
        request.getfixturevalue(portfolio_model),
        "asset",
        sorting_columns=[{"columns": ["ticker_asset", "date"], "ascending": [True, False]}],
    ).equals(request.getfixturevalue(curr_val))
