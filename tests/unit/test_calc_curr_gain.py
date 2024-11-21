"""Modelling unit tests."""

import numpy as np
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
            "trans_val_asset": [-100, 130, 600, 0, 0, 120, 0, -1000],
            "curr_val_asset": [1150, 1000, 950, 1500, 1080, 1210, 1200, 1100],
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
                "2023-12-31",
            ],
            "trans_val_asset": [-100, 130, 600, 0, 0, 120, 0, -1000, 0],
            "curr_val_asset": [1150, 1000, 950, 1500, 1080, 1210, 1200, 1100, np.nan],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def curr_perc_gain_1() -> pd.DataFrame:
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
            "curr_abs_gain_asset": [900.0, 850.0, 620.0, 200.0, 330.0, 200.0, 0.0],
            "curr_perc_gain_asset": [81.82, 85.0, 62.0, 20.0, 33.0, 20.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def curr_perc_gain_2() -> pd.DataFrame:
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
            "curr_abs_gain_asset": [900.0, 850.0, 620.0, 200.0, 330.0, 200.0, 100, 0],
            "curr_perc_gain_asset": [81.82, 85.0, 62.0, 20.0, 33.0, 20.0, 10.0, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("transactions", "curr_perc_gain"),
    [
        ("transactions_1", "curr_perc_gain_1"),
        ("transactions_2", "curr_perc_gain_2"),
    ],
)
def test_calc_curr_gain(
    transactions: str,
    curr_perc_gain: str,
    request: FixtureRequest,
) -> None:
    """Test calc_curr_gain.

    :param transactions: Transactions.
    :param curr_perc_gain: Resulting dataframe with the percent gain.
    :param request: FixtureRequest.
    """
    assert utils.calc_curr_gain(
        request.getfixturevalue(transactions),
        "asset",
        sorting_columns=[{"columns": ["date"], "ascending": [False]}],
    ).equals(request.getfixturevalue(curr_perc_gain))
