import requests
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
    tickers: list[list]
    start_date: pd.Timestamp
    end_date: pd.Timestamp


def preprocess():
    portfolio_data = _load_portfolio_data()

    stock_prices = _load_historical_stock_prices_yf(portfolio_data)
    print(stock_prices)

    # splits_data = _load_split_history(portfolio_data)
    # print(splits_data)
    #


def _load_portfolio_data():
    transactions = pd.read_json(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "../data/transactions.json"
        )
    )
    tickers = []
    for e in transactions["ticker"].unique():
        tickers.append(e.split(","))
    transactions["ticker"] = transactions["ticker"].apply(lambda x: x.split(",")[0])

    portfolio_data = PortfolioData(
        transactions=transactions,
        tickers=tickers,
        start_date=min(transactions["date"]),
        end_date=pd.Timestamp.today(),
    )

    return portfolio_data


def _load_historical_stock_prices_yf(portfolio_data: PortfolioData):
    stock_prices = []

    for ticker in portfolio_data.tickers:
        main_ticker = ticker[0]
        for ticker_try in ticker:
            stock_price = (
                yf.download(
                    ticker_try,
                    start=portfolio_data.start_date,
                    end=portfolio_data.start_date,
                )[["Open"]]
                .reset_index()
                .rename(columns={"Open": "open", "Date": "date"})
            )
            if not stock_price.empty:
                break
        stock_price["ticker"] = main_ticker
        stock_prices.append(stock_price)

    stock_prices = pd.concat(stock_prices)

    stock_prices = stock_prices[
        (stock_prices["date"] >= portfolio_data.start_date)
        & (stock_prices["date"] <= portfolio_data.end_date)
    ].reset_index()

    return stock_prices


def _load_split_history(portfolio_data: PortfolioData):
    split_historys = []

    for ticker in portfolio_data.tickers:
        main_ticker = ticker[0]
        for ticker_try in ticker:
            response = requests.get(
                f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_split/{ticker_try}?apikey={API_KEY}"
            )
            if response.status_code == 200:
                data = response.json()["historical"]
                split_history = pd.DataFrame(
                    {
                        "date": [x["date"] for x in data],
                        "split": [x["numerator"] / x["denominator"] for x in data],
                    }
                )
                split_history["ticker"] = main_ticker
                split_historys.append(split_history)
                break

    split_history = pd.concat(split_historys).reset_index(drop=True)
    split_history["date"] = pd.to_datetime(split_history["date"])
    split_history = split_history[
        (split_history["date"] >= portfolio_data.start_date)
        & (split_history["date"] <= portfolio_data.end_date)
    ]
    split_history = split_history[split_history["split"] >= 1]

    return split_historys


if __name__ == "__main__":
    preprocess()
