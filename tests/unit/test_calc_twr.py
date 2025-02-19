"""Test calc_twr()."""

import pandas as pd
import pytest
from pytest import FixtureRequest  # noqa: PT013

import stock_portfolio_tracker.modelling._utils as utils


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

@pytest.mark.parametrize(
    ("portfolio_model", "twr"),
    [
        ("portfolio_model_1", "twr_1"),
    ],
)
def test_calc_twr(
    portfolio_model: str,
    twr: str,
    request: FixtureRequest,
) -> None:
    """Test calc_twr().

    Args:
        portfolio_model: Input portfolio_model.
        twr: Resulting dataframe with the percent gain.
        request: FixtureRequest.
    """
    assert utils.calc_twr(
        request.getfixturevalue(portfolio_model),
        "asset",
    ).equals(request.getfixturevalue(twr))
