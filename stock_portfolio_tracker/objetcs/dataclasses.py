"""Module to store various objects."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class Config:
    """Config data."""

    portfolio_currency: str
    benchmark_tickers: list[str]


@dataclass
class PortfolioData:
    """Portfolio data."""

    transactions: pd.DataFrame
    assets_info: dict
    start_date: pd.Timestamp
    end_date: pd.Timestamp
