from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf  # type: ignore

from stock_portfolio_tracker import utils


class DataApi(ABC):
    @abstractmethod
    def get_ticker_name(self, ticker: str) -> str:
        """Get the name of the ticker.

        Args:
            ticker: Ticker symbol.

        Returns:
            Name of the ticker.
        """

    @abstractmethod
    def get_ticker_currency(self, ticker: str) -> str:
        """Get the currency of the ticker.

        Args:
            ticker: Ticker symbol.

        Returns:
            Name of the ticker.
        """

    @abstractmethod
    def get_asset_historical_data(self, ticker: str, start_date: pd.Timestamp) -> pd.DataFrame:
        """Get the historical data of the asset.

        Args:
            ticker: Ticker symbol.
            start_date: Start date for the historical data.

        Returns:
            DataFrame with the historical data of the asset.
        """

    @abstractmethod
    def get_currency_exchange_rate(
        self, origin_currency: str, local_currency: str, start_date: pd.Timestamp
    ) -> pd.DataFrame:
        """Get the exchange rate between two currencies.

        Args:
            origin_currency: Origin currency symbol.
            local_currency: Local currency symbol.
            start_date: Start date for the exchange rate data.

        Returns:
            DataFrame with the exchange rate data between the two currencies.
        """


class YahooFinanceApi(DataApi):
    def __init__(self) -> None:
        self.api = yf.Ticker

    def get_ticker_name(self, ticker: str) -> str:
        """Get the name of the ticker.

        Args:
            ticker: Ticker symbol.

        Returns:
            Name of the ticker.
        """
        return self.api(ticker).info.get("shortName")  # type: ignore

    def get_ticker_currency(self, ticker: str) -> str:
        """Get the currency of the ticker.

        Args:
            ticker: Ticker symbol.

        Returns:
            Name of the ticker.
        """
        return self.api(ticker).info.get("currency")  # type: ignore

    def get_asset_historical_data(self, ticker: str, start_date: pd.Timestamp) -> pd.DataFrame:
        """Get the historical data of the asset.

        Args:
            ticker: Ticker symbol.
            start_date: Start date for the historical data.

        Returns:
            DataFrame with the historical data of the asset.
        """
        return (  # type: ignore
            self.api(ticker)
            .history(start=start_date)[["Close", "Stock Splits", "Dividends"]]
            .sort_index(ascending=False)
            .reset_index()
            .rename(
                columns={
                    "Close": "close_adj_origin_currency",
                    "Date": "date",
                    "Stock Splits": "split",
                    "Dividends": "close_adj_origin_currency_dividends",
                },
            )
            .assign(date=lambda df: pd.to_datetime(df["date"].dt.strftime("%Y-%m-%d")))
        )

    def get_currency_exchange_rate(
        self, origin_currency: str, local_currency: str, start_date: pd.Timestamp
    ) -> pd.DataFrame:
        """Get the exchange rate between two currencies.

        Args:
            origin_currency: Origin currency symbol.
            local_currency: Local currency symbol.
            start_date: Start date for the exchange rate data.

        Returns:
            DataFrame with the exchange rate data between the two currencies.
        """
        ticker = f"{local_currency}{origin_currency}=X"

        return (  # type: ignore
            self.api(ticker)
            .history(start=start_date)[["Close"]]
            .sort_index(ascending=False)
            .reset_index()
            .rename(columns={"Close": "close_currency_rate", "Date": "date"})
            .assign(date=lambda df: pd.to_datetime(df["date"].dt.strftime("%Y-%m-%d")))
        )


class TestingApi(DataApi):
    def __init__(self) -> None:
        self.api = yf.Ticker

    def get_ticker_name(self, ticker: str) -> str:  # noqa: ARG002
        """Get the name of the ticker.

        Args:
            ticker: Ticker symbol.

        Returns:
            Name of the ticker.
        """
        return "NA"

    def get_ticker_currency(self, ticker: str) -> str:  # noqa: ARG002
        """Get the currency of the ticker.

        Args:
            ticker: Ticker symbol.

        Returns:
            Name of the ticker.
        """
        return "USD"

    def get_asset_historical_data(
        self,
        ticker: str,
        start_date: pd.Timestamp,  # noqa: ARG002
    ) -> pd.DataFrame:
        """Get the historical data of the asset.

        Args:
            ticker: Ticker symbol.
            start_date: Start date for the historical data.

        Returns:
            DataFrame with the historical data of the asset.
        """
        return utils.load_pickle(
            file_path=Path("tests/integration/api_mocked_artifacts"), file_name=f"{ticker}_data.pkl"
        )

    def get_currency_exchange_rate(
        self,
        origin_currency: str,  # noqa: ARG002
        local_currency: str,  # noqa: ARG002
        start_date: pd.Timestamp,  # noqa: ARG002
    ) -> pd.DataFrame | Any:
        """Get the exchange rate between two currencies.

        Args:
            origin_currency: Origin currency symbol.
            local_currency: Local currency symbol.
            start_date: Start date for the exchange rate data.

        Returns:
            DataFrame with the exchange rate data between the two currencies.
        """
        return utils.load_pickle(
            file_path=Path("tests/integration/api_mocked_artifacts"),
            file_name="currency_exchange_rate.pkl",
        )
