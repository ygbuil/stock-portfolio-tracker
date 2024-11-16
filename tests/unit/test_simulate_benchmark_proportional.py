"""Modelling unit tests."""

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from pytest import FixtureRequest  # noqa: PT013
from stock_portfolio_tracker.modelling._modelling_benchmark import _simulate_benchmark_proportional


@pytest.fixture()
def df_input_1() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-08",
                "2024-01-07",
                "2024-01-06",
                "2024-01-05",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
            ],
            "ticker_benchmark": ["IUSA.DE"] * 8,
            "split_benchmark": [0] * 8,
            "close_unadj_local_currency_benchmark": [140, 620, 600, 600, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "curr_qty_asset": [7, 7, 8, 5, 5, 5, 2, np.nan],
            "close_unadj_local_currency_asset": [1000, 950, 900, 1100, 1200, 1000, 1100, 1000],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def df_input_2() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-08",
                "2024-01-07",
                "2024-01-06",
                "2024-01-05",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
            ],
            "ticker_benchmark": ["IUSA.DE"] * 8,
            "split_benchmark": [0, 0, 0, 0, 0, 10, 0, 0],
            "close_unadj_local_currency_benchmark": [140, 620, 600, 600, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "trans_qty_asset": [0, -10, 30, 0, 0, 30, 2, 0],
            "curr_qty_asset": [70, 70, 80, 50, 50, 50, 2, np.nan],
            "close_unadj_local_currency_asset": [100, 95, 90, 110, 120, 100, 1100, 1000],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def df_output_1() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-08",
                "2024-01-07",
                "2024-01-06",
                "2024-01-05",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
            ],
            "ticker_benchmark": ["IUSA.DE"] * 8,
            "split_benchmark": [0] * 8,
            "close_unadj_local_currency_benchmark": [140, 620, 600, 600, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "curr_qty_asset": [7, 7, 8, 5, 5, 5, 2, np.nan],
            "close_unadj_local_currency_asset": [1000, 950, 900, 1100, 1200, 1000, 1100, 1000],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
            "trans_qty_benchmark": [0.0, -2.0, 6.0, 0.0, 0.0, 6.0, 4.0, 0.0],
            "trans_val_benchmark": [0.0, 1240.0, -3600.0, 0.0, 0.0, -3480.0, -2200.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture()
def df_output_2() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-08",
                "2024-01-07",
                "2024-01-06",
                "2024-01-05",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
            ],
            "ticker_benchmark": ["IUSA.DE"] * 8,
            "split_benchmark": [0, 0, 0, 0, 0, 10, 0, 0],
            "close_unadj_local_currency_benchmark": [140, 620, 600, 600, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "trans_qty_asset": [0, -10, 30, 0, 0, 30, 2, 0],
            "curr_qty_asset": [70, 70, 80, 50, 50, 50, 2, np.nan],
            "close_unadj_local_currency_asset": [100, 95, 90, 110, 120, 100, 1100, 1000],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
            "trans_qty_benchmark": [0.0, -2.0, 6.0, 0.0, 0.0, 6.0, 4.0, 0.0],
            "trans_val_benchmark": [0.0, 1240.0, -3600.0, 0.0, 0.0, -3480.0, -2200.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("df_input", "df_output"),
    [
        ("df_input_1", "df_output_1"),
        ("df_input_2", "df_output_2"),
    ],
)
def test_simulate_benchmark_proportional(
    df_input: str,
    df_output: str,
    request: FixtureRequest,
) -> None:
    """Test simulate_benchmark_proportional.

    :param df_input: Input dataframe.
    :param df_output: Output dataframe.
    :param request: FixtureRequest.
    """
    assert_frame_equal(
        _simulate_benchmark_proportional(request.getfixturevalue(df_input)),
        request.getfixturevalue(df_output),
        rtol=1e-7,
        atol=1e-8,
    )
