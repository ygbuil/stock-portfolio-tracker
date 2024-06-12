"""Modelling unit tests."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture()
def transactions() -> pd.DataFrame:
    """Transsactions."""
    return pd.DataFrame(
        {
            "date": [
                "2024-01-01",
                "2024-01-02",
                "2024-01-03",
                "2024-01-04",
                "2024-01-05",
                "2024-01-06",
                "2024-01-06",
                "2024-01-07",
            ],
            "value": [-1000, np.nan, 120, np.nan, np.nan, -600, 130, -100],
            "current_portfolio_value": [0, 1100, 1200, 1080, 1300, 1500, 1000],
        },
    )
