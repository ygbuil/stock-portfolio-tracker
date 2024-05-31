import os
import pandas as pd
import yfinance as yf
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv("API_KEY")


@dataclass
class PortfolioData:
    transactions: pd.DataFrame
    tickers: list[str]
    currencies: list[str]
    start_date: pd.Timestamp
    end_date: pd.Timestamp


def preprocess():
    portfolio_data = _load_portfolio_data()
    print(portfolio_data)

    stock_prices = _load_historical_stock_prices(portfolio_data)
    print(stock_prices)

    _load_currency_exchange(
        portfolio_data,
    )

    tickers_benchmarks = ["SXR8.DE"]
    _load_benchmark_data(portfolio_data, tickers_benchmarks)


def _load_portfolio_data():
    transactions = pd.read_csv(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/transactions.csv"
        )
    ).astype(
        {
            "date": str,
            "transaction_type": str,
            "stock_name": str,
            "stock_ticker": str,
            "origin_currency": str,
            "price_paid": float,
        }
    )

    transactions["date"] = pd.to_datetime(transactions["date"])

    return PortfolioData(
        transactions=transactions,
        tickers=transactions["stock_ticker"].unique(),
        currencies=transactions["origin_currency"].unique(),
        start_date=min(transactions["date"]),
        end_date=pd.Timestamp.today(),
    )


def _load_historical_stock_prices(portfolio_data: PortfolioData):
    stock_prices = []

    for ticker in portfolio_data.tickers:
        stock_price = _load_time_series(portfolio_data, ticker)
        stock_prices.append(stock_price)

    return (
        pd.concat(stock_prices)
        .sort_values(by="date", ascending=False)
        .groupby("ticker")
        .first()
        .reset_index()
    )


def _load_time_series(portfolio_data, ticker):
    time_series = (
        yf.download(
            ticker,
            start=portfolio_data.start_date,
            end=portfolio_data.end_date,
        )[["Open"]]
        .reset_index()
        .rename(columns={"Open": "open", "Date": "date"})
    )
    time_series["ticker"] = ticker

    return time_series


def _load_currency_exchange(portfolio_data, local_currency, origin_currencies):
    benchmarks = []

    for origin_currency in origin_currencies:
        benchmark = _load_time_series(
            portfolio_data, f"{local_currency}{origin_currency}=X"
        )
        benchmarks.append(benchmark)

    benchmarks = pd.concat(benchmarks).reset_index()

    return benchmarks


def _load_benchmark_data(portfolio_data, tickers_benchmarks):
    benchmarks = []

    for ticker_benchmark in tickers_benchmarks:
        benchmark = _load_time_series(portfolio_data, ticker_benchmark)
        benchmarks.append(benchmark)

    benchmarks = pd.concat(benchmarks).reset_index()

    return benchmarks


if __name__ == "__main__":
    preprocess()
