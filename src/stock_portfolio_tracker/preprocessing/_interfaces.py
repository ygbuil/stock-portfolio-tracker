from abc import ABC, abstractmethod

import pandas as pd
import yfinance as yf  # type: ignore


class DataApi(ABC):
    @abstractmethod
    def get_ticker_name(self, ticker: str) -> str:
        """Get the name of the ticker."""

    @abstractmethod
    def get_ticker_currency(self, ticker: str) -> str:
        """Get the currency of the ticker."""

    @abstractmethod
    def get_asset_historical_data(self, ticker: str, start_date: pd.Timestamp) -> pd.DataFrame:
        """Get historical data for a ticker."""

    @abstractmethod
    def get_currency_exchange_rate(
        self, origin_currency: str, local_currency: str, start_date: pd.Timestamp
    ) -> pd.DataFrame:
        """Get the exchange rate between two currencies."""


class YahooFinanceApi(DataApi):
    def __init__(self) -> None:
        self.api = yf.Ticker

    def get_ticker_name(self, ticker: str) -> str:
        return self.api(ticker).info.get("shortName")  # type: ignore

    def get_ticker_currency(self, ticker: str) -> str:
        return self.api(ticker).info.get("currency")  # type: ignore

    def get_asset_historical_data(self, ticker: str, start_date: pd.Timestamp) -> pd.DataFrame:
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
        ticker = f"{local_currency}{origin_currency}=X"

        return (  # type: ignore
            self.api(ticker)
            .history(start=start_date)[["Close"]]
            .sort_index(ascending=False)
            .reset_index()
            .rename(columns={"Close": "close_currency_rate", "Date": "date"})
            .assign(date=lambda df: pd.to_datetime(df["date"].dt.strftime("%Y-%m-%d")))
        )
