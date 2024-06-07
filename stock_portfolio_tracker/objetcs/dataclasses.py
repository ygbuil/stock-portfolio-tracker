"""Module to store various objects."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class PortfolioData:
    """Portfolio data."""

    transactions: pd.DataFrame
    tickers: list[str]
    currencies: list[str]
    start_date: pd.Timestamp
    end_date: pd.Timestamp
