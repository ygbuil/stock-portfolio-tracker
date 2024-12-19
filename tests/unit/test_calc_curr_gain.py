"""Test _calc_curr_gain()."""

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
def portfolio_model_2() -> pd.DataFrame:
    """Test random buys and sells 2.

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
                "2023-12-31",
            ],
            "trans_val_asset": [-100, 130, 600, 0, 0, 120, 0, -1000, 0],
            "curr_val_asset": [1150, 1000, 950, 1500, 1080, 1210, 1200, 1100, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def portfolio_model_3() -> pd.DataFrame:
    """Test complete buys and sells of the same position.

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
                "2023-12-31",
            ],
            "trans_val_asset": [700, 100, -600, 0, 0, 1250, 0, -1000, 0],
            "curr_val_asset": [0, 700, 650, 0, 0, 0, 1200, 1100, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.fixture
def curr_gain_1() -> pd.DataFrame:
    """Test random buys and sells 1.

    Returns:
        Dataframe with absolute and percentual current gain.
    """
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
def curr_gain_2() -> pd.DataFrame:
    """Test random buys and sells 2.

    Returns:
        Dataframe with absolute and percentual current gain.
    """
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


@pytest.fixture
def curr_gain_3() -> pd.DataFrame:
    """Test complete buys and sells of the same position.

    Returns:
        Dataframe with absolute and percentual current gain.
    """
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
            "curr_abs_gain_asset": [450.0, 450.0, 250.0, 250.0, 250.0, 200.0, 100, 0],
            "curr_perc_gain_asset": [28.12, 28.12, 25.0, 25.0, 25.0, 20.0, 10.0, 0],
        },
    ).assign(date=lambda df: pd.to_datetime(df["date"], format="%Y-%m-%d"))


@pytest.mark.parametrize(
    ("portfolio_model", "curr_gain"),
    [
        ("portfolio_model_1", "curr_gain_1"),
        ("portfolio_model_2", "curr_gain_2"),
        ("portfolio_model_3", "curr_gain_3"),
    ],
)
def test_calc_curr_gain(
    portfolio_model: str,
    curr_gain: str,
    request: FixtureRequest,
) -> None:
    """Test calc_curr_gain().

    Args:
        portfolio_model: Input portfolio_model.
        curr_gain: Resulting dataframe with the percent gain.
        request: FixtureRequest.
    """
    assert utils.calc_curr_gain(
        request.getfixturevalue(portfolio_model),
        "asset",
        sorting_columns=[{"columns": ["date"], "ascending": [False]}],
    ).equals(request.getfixturevalue(curr_gain))
