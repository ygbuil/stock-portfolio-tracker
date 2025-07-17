"""Test calc_twr()."""

import pandas as pd
import pytest
from pytest import FixtureRequest  # noqa: PT013

import stock_portfolio_tracker.modelling._utils as utils
from stock_portfolio_tracker.utils import Freq, PositionType


@pytest.fixture
def portfolio_model_1() -> pd.DataFrame:
    """Test random buys and sells 1.

    Returns:
        Portfolio model.
    """
    return pd.DataFrame(
        {
            "date": [
                "2024-12-31",
                "2024-12-30",
                "2024-12-29",
                "2024-12-28",
                "2024-12-27",
                "2024-12-26",
                "2024-12-25",
                "2024-12-24",
            ],
            "trans_val_asset": [-100, 130, 600, 0, 0, 120, 0, -1000],
            "curr_val_asset": [1150, 1000, 950, 1500, 1080, 1210, 1200, 1100],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def portfolio_model_2() -> pd.DataFrame:
    """Test random buys and sells 1.

    Returns:
        Portfolio model.
    """
    return pd.DataFrame(
        {
            "date": [
                "2025-01-05",
                "2025-01-04",
                "2025-01-03",
                "2025-01-02",
                "2025-01-01",
                "2024-12-31",
                "2024-12-30",
                "2024-12-29",
                "2024-12-28",
                "2024-12-27",
                "2024-12-26",
                "2024-12-25",
                "2024-12-24",
            ],
            "trans_val_asset": [0, 200, 0, 0, 0, -100, 130, 600, 0, 0, 120, 0, -1000],
            "curr_val_asset": [
                1100,
                800,
                1100,
                1300,
                1200,
                1150,
                1000,
                950,
                1500,
                1080,
                1210,
                1200,
                1100,
            ],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def twr_1() -> pd.DataFrame:
    """Test random buys and sells 1.

    Returns:
        Dataframe with absolute and percentual current gain.
    """
    return pd.DataFrame(
        {
            "year": [
                2024,
            ],
            "twr_asset": [55.52],
        }
    )


@pytest.fixture
def twr_2() -> pd.DataFrame:
    """Test random buys and sells 1.

    Returns:
        Dataframe with absolute and percentual current gain.
    """
    return pd.DataFrame(
        {
            "year": [
                2025,
                2024,
            ],
            "twr_asset": [26.04, 55.52],
        }
    )


@pytest.fixture
def twr_3() -> pd.DataFrame:
    """Test random buys and sells 1.

    Returns:
        Dataframe with absolute and percentual current gain.
    """
    return pd.DataFrame(
        {
            "year": [
                0.03,
            ],
            "twr_asset": [77.87],
        }
    )


@pytest.mark.parametrize(
    ("portfolio_model", "twr", "freq"),
    [
        ("portfolio_model_1", "twr_1", Freq.YEARLY),
        ("portfolio_model_2", "twr_2", Freq.YEARLY),
        ("portfolio_model_2", "twr_3", Freq.ALL),
    ],
)
def test_calc_twr(
    portfolio_model: str,
    twr: str,
    freq: Freq,
    request: FixtureRequest,
) -> None:
    """Test calc_twr().

    Args:
        portfolio_model: Input portfolio_model.
        twr: Resulting dataframe with the percent gain.
        freq: Frequency on which to calculate TWR.
        request: FixtureRequest.
    """
    assert utils.calc_twr(
        request.getfixturevalue(portfolio_model), PositionType.ASSET, freq
    ).equals(request.getfixturevalue(twr))
