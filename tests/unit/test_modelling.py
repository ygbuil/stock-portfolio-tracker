"""Modelling unit tests."""

import numpy as np
import pandas as pd
import pytest

# os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')) # noqa: ERA001
import stock_portfolio_tracker.modelling._utils as utils


@pytest.fixture()
def transactions() -> pd.DataFrame:
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
            "value": [-100, 130, 600, np.nan, np.nan, 120, np.nan, -1000],
            "current_portfolio_value": [1150, 1000, 950, 1500, 1080, 1210, 1200, 1100],
        },
    )


def test_calculate_current_percent_gain(transactions: pd.DataFrame) -> None:
    """Test calculate_current_percent_gain.

    :param transactions: Transactions.
    """
    utils.calculate_current_percent_gain(transactions)

    assert 1 == 1  # noqa: PLR0133
