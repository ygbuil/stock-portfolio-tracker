import requests
import os
import pandas as pd
import yfinance as yf
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()
API_KEY = os.getenv('API_KEY')


@dataclass
class InputData:
    transactions: pd.DataFrame
    tickers: list[list]
    start_date: str


def preprocess():
    input_data = _load_input_data()
    
    stock_prices = _load_historical_stock_prices_yf(input_data.tickers)
    print(stock_prices)
    
    splits_data = _load_split_history(input_data)
    print(splits_data)
    

def _load_input_data():
    transactions = pd.read_json(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/transactions.json"))
    tickers = []
    for e in transactions["ticker"].unique():
        tickers.append(e.split(","))
    transactions["ticker"] = transactions["ticker"].apply(lambda x: x.split(",")[0])

    input_data = InputData(transactions=transactions, tickers=tickers, start_date=min(transactions["date"]))

    return input_data


def _load_historical_stock_prices_yf(tickers: list):
    stock_prices = []

    for ticker in tickers:
        main_ticker = ticker[0]
        for ticker_try in ticker:
            stock_price = yf.download(ticker_try, start="2000-01-01", end="2024-05-28")[["Open"]].reset_index().rename(columns={"Open": "open", "Date": "date"})
            if not stock_price.empty:
                break
        stock_price["ticker"] = main_ticker
        stock_prices.append(stock_price)

    return pd.concat(stock_prices)


def _load_split_history(input_data: InputData):
    split_historys = []

    for ticker in input_data.tickers:
        main_ticker = ticker[0]
        for ticker_try in ticker:
            response = requests.get(f"https://financialmodelingprep.com/api/v3/historical-price-full/stock_split/{ticker_try}?apikey={API_KEY}")
            if response.status_code == 200:
                data = response.json()["historical"]
                split_history = pd.DataFrame({"date": [x["date"] for x in data], "split": [x["numerator"]/x["denominator"] for x in data]})
                split_history["ticker"] = main_ticker
                split_historys.append(split_history)
                break

    split_historys = pd.concat(split_historys).reset_index(drop=True)
    split_historys["date"] = pd.to_datetime(split_historys["date"])
    split_historys = split_historys[split_historys["date"] >= input_data.start_date]

    return split_historys

    
if __name__ == "__main__":
    preprocess()
    