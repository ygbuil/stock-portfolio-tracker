"""Test _simulate_benchmark_proportional()."""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal
from pytest import FixtureRequest  # noqa: PT013

from stock_portfolio_tracker.modelling._modelling_benchmark import _simulate_benchmark_proportional


@pytest.fixture
def portfolio_model_1() -> pd.DataFrame:
    """Test _simulate_benchmark_proportional() with random data.

    Returns:
        Portfolio model.
    """
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
            "split_benchmark": [1] * 8,
            "close_unadj_local_currency_benchmark": [140, 620, 600, 600, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "split_asset": [1] * 8,
            "close_unadj_local_currency_asset": [1000, 950, 900, 1100, 1200, 1000, 1100, 1000],
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [7, 7, 8, 5, 5, 5, 2, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def portfolio_model_2() -> pd.DataFrame:
    """Test _simulate_benchmark_proportional() with transaction on split day.

    Returns:
        Portfolio model.
    """
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
            "split_benchmark": [1] * 8,
            "close_unadj_local_currency_benchmark": [140, 620, 600, 600, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "split_asset": [1, 1, 1, 1, 1, 10, 1, 1],
            "close_unadj_local_currency_asset": [100, 95, 90, 110, 120, 100, 1100, 1000],
            "trans_qty_asset": [0, -10, 30, 0, 0, 30, 2, 0],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [70, 70, 80, 50, 50, 50, 2, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def portfolio_model_3() -> pd.DataFrame:
    """Test _simulate_benchmark_proportional() with random data.

    Returns:
        Portfolio model.
    """
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
            "split_benchmark": [1, 1, 1, 10, 1, 1, 1, 1],
            "close_unadj_local_currency_benchmark": [14, 62, 60, 60, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "split_asset": [1] * 8,
            "close_unadj_local_currency_asset": [1000, 950, 900, 1100, 1200, 1000, 1100, 1000],
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [7, 7, 8, 5, 5, 5, 2, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def portfolio_model_4() -> pd.DataFrame:
    """Test _simulate_benchmark_proportional() with complet sell of position and then re-enter.

    Returns:
        Portfolio model.
    """
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
            "split_benchmark": [1] * 8,
            "close_unadj_local_currency_benchmark": [140, 620, 600, 800, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "split_asset": [1] * 8,
            "close_unadj_local_currency_asset": [1000, 950, 900, 1100, 1200, 1000, 1100, 1000],
            "trans_qty_asset": [0, 0, 0, 2, -2, 0, 2, 0],
            "trans_val_asset": [0, 0, 0, -2200, 2400, 0, -2200, 0],
            "curr_qty_asset": [2, 2, 2, 2, 0, 2, 2, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def benchmark_proportional_1() -> pd.DataFrame:
    """Test _simulate_benchmark_proportional() without transaction on split day.

    Returns:
        Dataframe with benchmark simulation.
    """
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
            "split_benchmark": [1] * 8,
            "close_unadj_local_currency_benchmark": [140, 620, 600, 600, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "split_asset": [1] * 8,
            "close_unadj_local_currency_asset": [1000, 950, 900, 1100, 1200, 1000, 1100, 1000],
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [7, 7, 8, 5, 5, 5, 2, 0],
            "trans_qty_benchmark": [0.0, -2.0, 6.0, 0.0, 0.0, 6.0, 4.0, 0.0],
            "trans_val_benchmark": [0.0, 1240.0, -3600.0, 0.0, 0.0, -3480.0, -2200.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def benchmark_proportional_2() -> pd.DataFrame:
    """Test _simulate_benchmark_proportional() with transaction on split day.

    Returns:
        Dataframe with benchmark simulation.
    """
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
            "split_benchmark": [1] * 8,
            "close_unadj_local_currency_benchmark": [140, 620, 600, 600, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "split_asset": [1, 1, 1, 1, 1, 10, 1, 1],
            "close_unadj_local_currency_asset": [100, 95, 90, 110, 120, 100, 1100, 1000],
            "trans_qty_asset": [0, -10, 30, 0, 0, 30, 2, 0],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [70, 70, 80, 50, 50, 50, 2, 0],
            "trans_qty_benchmark": [0.0, -2.0, 6.0, 0.0, 0.0, 6.0, 4.0, 0.0],
            "trans_val_benchmark": [0.0, 1240.0, -3600.0, 0.0, 0.0, -3480.0, -2200.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def benchmark_proportional_3() -> pd.DataFrame:
    """Test _simulate_benchmark_proportional() without transaction on split day.

    Returns:
        Dataframe with benchmark simulation.
    """
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
            "split_benchmark": [1, 1, 1, 10, 1, 1, 1, 1],
            "close_unadj_local_currency_benchmark": [14, 62, 60, 60, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "split_asset": [1] * 8,
            "close_unadj_local_currency_asset": [1000, 950, 900, 1100, 1200, 1000, 1100, 1000],
            "trans_qty_asset": [0, -1, 3, 0, 0, 3, 2, 0],
            "trans_val_asset": [0, 950, -1800, 0, 0, -3000, -2200, 0],
            "curr_qty_asset": [7, 7, 8, 5, 5, 5, 2, 0],
            "trans_qty_benchmark": [0.0, -20.0, 60.0, 0.0, 0.0, 6.0, 4.0, 0.0],
            "trans_val_benchmark": [0.0, 1240.0, -3600.0, 0.0, 0.0, -3480.0, -2200.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def benchmark_proportional_4() -> pd.DataFrame:
    """Test _simulate_benchmark_proportional() with complet sell of position and then re-enter.

    Returns:
        Dataframe with benchmark simulation.
    """
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
            "split_benchmark": [1] * 8,
            "close_unadj_local_currency_benchmark": [140, 620, 600, 800, 540, 580, 550, 100],
            "ticker_asset": ["NVDA"] * 8,
            "split_asset": [1] * 8,
            "close_unadj_local_currency_asset": [1000, 950, 900, 1100, 1200, 1000, 1100, 1000],
            "trans_qty_asset": [0, 0, 0, 2, -2, 0, 2, 0],
            "trans_val_asset": [0, 0, 0, -2200, 2400, 0, -2200, 0],
            "curr_qty_asset": [2, 2, 2, 2, 0, 2, 2, 0],
            "trans_qty_benchmark": [0.0, 0.0, 0.0, 2.75, -4.0, 0.0, 4.0, 0.0],
            "trans_val_benchmark": [0.0, 0.0, 0.0, -2200, 2160.0, 0.0, -2200.0, 0.0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("portfolio_model", "benchmark_proportional"),
    [
        ("portfolio_model_1", "benchmark_proportional_1"),
        ("portfolio_model_2", "benchmark_proportional_2"),
        ("portfolio_model_3", "benchmark_proportional_3"),
        ("portfolio_model_4", "benchmark_proportional_4"),
    ],
)
def test_simulate_benchmark_proportional(
    portfolio_model: str,
    benchmark_proportional: str,
    request: FixtureRequest,
) -> None:
    """Test _simulate_benchmark_proportional().

    Args:
        portfolio_model: Input dataframe.
        benchmark_proportional: Output dataframe.
        request: FixtureRequest.
    """
    assert_frame_equal(
        _simulate_benchmark_proportional(request.getfixturevalue(portfolio_model)),
        request.getfixturevalue(benchmark_proportional),
        rtol=1e-7,
        atol=1e-8,
    )
