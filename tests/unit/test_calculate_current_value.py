"""Modelling unit tests."""

import numpy as np
import pandas as pd
import pytest
from pytest import FixtureRequest  # noqa: PT013

import stock_portfolio_tracker.modelling._utils as utils


@pytest.fixture()
def df_input_1() -> pd.DataFrame:
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
            "split_asset": [0, 0, 0, 0, 10, 0, 0, 0],
            "close_unadjusted_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "quantity_asset": [np.nan, -1, 3, np.nan, np.nan, 3, 2, np.nan],
            "value_asset": [np.nan, 100, -285, np.nan, np.nan, -3000, -2200, np.nan],
            "curr_qty_asset": [52, 52, 53, 50, 50, 5, 2, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def df_input_2() -> pd.DataFrame:
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
            "split_asset": [0, 0, 0, 0, 10, 0, 0, 0],
            "close_unadjusted_local_currency_asset": [110, 100, 95, 100, 90, 1000, 1100, 1000],
            "quantity_asset": [np.nan, -1, 3, np.nan, 4, 3, 2, np.nan],
            "value_asset": [np.nan, 100, -285, np.nan, -360, -3000, -2200, np.nan],
            "curr_qty_asset": [56, 56, 57, 54, 54, 5, 2, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def df_output_1() -> pd.DataFrame:
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
            "ticker_asset": ["NVDA"] * 7,
            "split_asset": [0, 0, 0, 10, 0, 0, 0],
            "close_unadjusted_local_currency_asset": [110, 100, 100, 90, 1000, 1100, 1000],
            "quantity_asset": [np.nan, -1, np.nan, np.nan, 3, 2, np.nan],
            "value_asset": [np.nan, 100, np.nan, np.nan, -3000, -2200, np.nan],
            "curr_qty_asset": [52, 52, 50, 50, 5, 2, np.nan],
            "curr_val_asset": [5720, 5200, 5000, 4500, 5000, 2200, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def df_output_2() -> pd.DataFrame:
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
            "ticker_asset": ["NVDA"] * 7,
            "split_asset": [0, 0, 0, 10, 0, 0, 0],
            "close_unadjusted_local_currency_asset": [110, 100, 100, 90, 1000, 1100, 1000],
            "quantity_asset": [np.nan, -1, np.nan, 4, 3, 2, np.nan],
            "value_asset": [np.nan, 100, np.nan, -360, -3000, -2200, np.nan],
            "curr_qty_asset": [56, 56, 54, 54, 5, 2, np.nan],
            "curr_val_asset": [6160, 5600, 5400, 4860, 5000, 2200, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("df_input", "df_output"),
    [
        ("df_input_1", "df_output_1"),
        ("df_input_2", "df_output_2"),
    ],
)
def test_calculate_curr_val(
    df_input: pd.DataFrame,
    df_output: pd.DataFrame,
    request: FixtureRequest,
) -> None:
    """Test calculate_curr_qty.

    :param df_input: Input dataframe.
    :param df_output: Output dataframe.
    :param request: FixtureRequest.
    """
    assert utils.calculate_curr_val(
        request.getfixturevalue(df_input),
        "asset",
    ).equals(request.getfixturevalue(df_output))
