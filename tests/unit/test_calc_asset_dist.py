"""Test _calc_asset_dist()."""

import pandas as pd
import pytest
from pytest import FixtureRequest  # noqa: PT013

from stock_portfolio_tracker.modelling._modelling_portfolio import _calc_asset_dist
from stock_portfolio_tracker.utils import PortfolioData, PositionType


@pytest.fixture
def portfolio_model_1() -> pd.DataFrame:
    """Test random buys and sells.

    Returns:
        Portfolio model.
    """
    return pd.DataFrame(
        {
            "date": [
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
                "2024-01-04",
                "2024-01-03",
                "2024-01-02",
                "2024-01-01",
            ],
            "ticker_asset": ["NVDA"] * 4 + ["MA"] * 4 + ["V"] * 4 + ["AMZN"] * 4,
            "curr_qty_asset": [2, 10, 10, 30, 5, 4, 4, 4, 0, 0, 10, 10, 12, 12, 12, 12],
            "curr_val_asset": [
                115,
                500,
                550,
                1500,
                1080,
                820,
                790,
                800,
                0,
                0,
                1200,
                1100,
                2000,
                1900,
                1900,
                1910,
            ],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def portfolio_data_1() -> PortfolioData:
    """Portfolio data.

    Returns:
        Portfolio data.
    """
    return PortfolioData(pd.DataFrame(), {}, pd.Timestamp("2024-01-01"), pd.Timestamp("2024-01-04"))


@pytest.fixture
def asset_distribution_1() -> pd.DataFrame:
    """Asset distribution.

    Returns:
        Asset distribution.
    """
    return pd.DataFrame(
        {
            "date": [
                "2024-01-04",
                "2024-01-04",
                "2024-01-04",
            ],
            "ticker_asset": ["AMZN", "MA", "NVDA"],
            "curr_qty_asset": [12, 5, 2],
            "curr_val_asset": [2000, 1080, 115],
            "percent": [62.60, 33.8, 3.6],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("portfolio_model", "portfolio_data", "asset_distribution"),
    [
        ("portfolio_model_1", "portfolio_data_1", "asset_distribution_1"),
    ],
)
def test_calc_asset_dist(
    portfolio_model: str,
    portfolio_data: str,
    asset_distribution: str,
    request: FixtureRequest,
) -> None:
    """Test _calc_simple_return_daily().

    Args:
        portfolio_model: Portfolio with curr_qty and curr_val for each asset.
        portfolio_data: Transactions history and other portfolio data.
        asset_distribution: Percentage and amount of each asset held.
        request: FixtureRequest.
    """
    assert _calc_asset_dist(
        request.getfixturevalue(portfolio_model),
        request.getfixturevalue(portfolio_data),
        PositionType.ASSET,
    ).equals(request.getfixturevalue(asset_distribution))
