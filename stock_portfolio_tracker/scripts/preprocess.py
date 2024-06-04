import os
import pandas as pd
import yfinance as yf
from dataclasses import dataclass
from dotenv import load_dotenv
import numpy as np
import matplotlib.pyplot as plt


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

    currency_exchanges = _load_currency_exchange(
        portfolio_data,
        "EUR",
    )

    stock_prices = _load_historical_stock_prices(portfolio_data, currency_exchanges)


    tickers_benchmarks = ["SXR8.DE"]
    benchmarks = _load_benchmark_data(portfolio_data, tickers_benchmarks)
    end_date = min(
        max(stock_prices["date"]),
        max(currency_exchanges["date"]),
        max(benchmarks["date"]),
    )

    _get_performance(
        portfolio_data, benchmarks, stock_prices, currency_exchanges, end_date
    )


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
            "quantity": float,
            "value": float,
        }
    )

    transactions["date"] = pd.to_datetime(transactions["date"], dayfirst=True)
    transactions["value"] = transactions.apply(
        lambda x: abs(x["value"])
        if x["transaction_type"] == "Sale"
        else -abs(x["value"]),
        axis=1,
    )
    transactions["quantity"] = transactions.apply(
        lambda x: -abs(x["quantity"])
        if x["transaction_type"] == "Sale"
        else abs(x["quantity"]),
        axis=1,
    )
    transactions = transactions.drop("transaction_type", axis=1)

    return PortfolioData(
        transactions=transactions,
        tickers=transactions["stock_ticker"].unique(),
        currencies=transactions["origin_currency"].unique(),
        start_date=min(transactions["date"]),
        end_date=pd.Timestamp.today(),
    )


def _load_historical_stock_prices(portfolio_data: PortfolioData, currency_exchange):
    stock_prices = []

    for ticker in portfolio_data.tickers:
        stock_price = _load_stock_data(
            ticker, portfolio_data.start_date, portfolio_data.end_date
        )
        stock_price["stock_ticker"] = ticker
        stock_prices.append(stock_price)

    stock_prices = pd.concat(stock_prices)


    stock_prices = pd.merge(
        stock_prices,
        currency_exchange,
        "left",
        left_on=["date", "origin_currency"],
        right_on=["date", "currency_exchange_rate_ticker"],
    )
    stock_prices["open_unadjusted_local_currency"] = (
        stock_prices["open_unadjusted_origin_currency"]
        / stock_prices["open_currency_rate"]
    )
    stock_prices = stock_prices[
        ["date", "stock_ticker", "open_unadjusted_local_currency", "stock_split"]
    ]

    return stock_prices


def _load_stock_data(ticker, start_date, end_date):
    stock = yf.Ticker(ticker)
    stock_price = (
        stock
        .history(start=start_date, end=end_date)[["Open", "Stock Splits"]]
        .sort_index(ascending=False)
        .reset_index()
        .rename(
            columns={
                "Open": "open_adjusted_origin_currency",
                "Date": "date",
                "Stock Splits": "stock_split",
            }
        )
    )


    stock_price["date"] = (
        stock_price["date"].dt.strftime("%Y-%m-%d").apply(lambda x: pd.Timestamp(x))
    )
    full_date_range = pd.DataFrame({"date": reversed(pd.date_range(start=start_date, end=end_date, freq='D'))})
    stock_price = pd.merge(full_date_range, stock_price, "left", on="date")
    stock_price["stock_split"] = stock_price["stock_split"].fillna(0)
    stock_price['open_adjusted_origin_currency'] = stock_price['open_adjusted_origin_currency'].bfill()
    stock_price['open_adjusted_origin_currency'] = stock_price['open_adjusted_origin_currency'].ffill()

    stock_price["stock_split_cumsum"] = (
        stock_price["stock_split"].replace(0, 1).cumprod()
    )
    stock_price["open_unadjusted_origin_currency"] = (
        stock_price["open_adjusted_origin_currency"] * stock_price["stock_split_cumsum"]
    )
    stock_price["origin_currency"] = stock.info.get('currency')
    


    return stock_price[["date", "open_unadjusted_origin_currency", "stock_split", "origin_currency"]]


def _load_currency_exchange(portfolio_data, local_currency):
    currency_exchanges = []

    for origin_currency in portfolio_data.currencies:
        if origin_currency != local_currency:
            currency_exchange = (
                yf.Ticker(f"{local_currency}{origin_currency}=X")
                .history(start=portfolio_data.start_date, end=portfolio_data.end_date)[
                    ["Open"]
                ]
                .sort_index(ascending=False)
                .reset_index()
                .rename(columns={"Open": "open_currency_rate", "Date": "date"})
            )
            currency_exchange["date"] = (
                currency_exchange["date"]
                .dt.strftime("%Y-%m-%d")
                .apply(lambda x: pd.Timestamp(x))
            )
            full_date_range = pd.DataFrame({"date": reversed(pd.date_range(start=portfolio_data.start_date, end=portfolio_data.end_date, freq='D'))})
            currency_exchange = pd.merge(full_date_range, currency_exchange, "left", on="date")
            currency_exchange['open_currency_rate'] = currency_exchange['open_currency_rate'].bfill()
            currency_exchange['open_currency_rate'] = currency_exchange['open_currency_rate'].ffill()
        else:
            currency_exchange = pd.DataFrame(
                {
                    "date": reversed(
                        pd.date_range(
                            start=portfolio_data.start_date, end=portfolio_data.end_date
                        )
                    ),
                    "open_currency_rate": 1,
                }
            )

        currency_exchange["currency_exchange_rate_ticker"] = origin_currency
        currency_exchanges.append(currency_exchange)

    currency_exchanges = pd.concat(currency_exchanges).reset_index(drop=True)

    return currency_exchanges


def _load_benchmark_data(portfolio_data, tickers_benchmarks):
    benchmarks = []

    for ticker_benchmark in tickers_benchmarks:
        benchmark = _load_stock_data(
            ticker_benchmark, portfolio_data.start_date, portfolio_data.end_date
        )
        benchmark["benchmark_ticker"] = ticker_benchmark
        benchmarks.append(benchmark)

    benchmarks = pd.concat(benchmarks).reset_index(drop=True)

    return benchmarks


def _get_performance(
    portfolio_data, benchmarks, stock_prices, currency_exchange, end_date
):

    aux = pd.merge(
        stock_prices, portfolio_data.transactions, "left", on=["date", "stock_ticker"]
    )

    grouped = aux.reset_index(drop=True).groupby('stock_ticker')
    aux = []
    for _, group in grouped:
        aux.append(_calculate_current_quantity(group))
    aux = pd.concat(aux)

    aux["portfolio_value"] = aux["current_quantity"] * aux["open_unadjusted_local_currency"]
    


    
    #portfolio_summary = aux.groupby("date")['portfolio_value'].agg(lambda x: np.nan if x.isna().all() else x.sum(skipna=True)).reset_index()
    #portfolio_summary = aux.groupby("date")['portfolio_value'].agg(lambda x: np.nan if x.isna().any() else x.sum(skipna=True)).reset_index()
    portfolio_summary = aux.groupby("date")['portfolio_value'].sum().reset_index()

   

    plt.figure(figsize=(10, 6))
    plt.plot(portfolio_summary['date'], portfolio_summary['portfolio_value'], marker='o', linestyle='-', color='b')
    plt.xlabel('Date')
    plt.ylabel('Portfolio Value')
    plt.title('Portfolio Value Over Time')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()




    # transactions_and_benchmark = pd.merge(
    #     stock_prices, portfolio_data.transactions, "left", on=["date", "stock_ticker"]
    # )
    # transactions_and_benchmark["equivalent_benchmark_sales_transaction"] = (
    #     -transactions_and_benchmark["value"] / transactions_and_benchmark["open"]
    # )

    # current_benchmar_value = benchmarks[benchmarks["date"] == end_date]["open"].iloc[0]
    # cash_flow = sum(transactions_and_benchmark["value"])
    # benchmark_portfolio_current_value = (
    #     sum(transactions_and_benchmark["equivalent_benchmark_sales_transaction"])
    #     * current_benchmar_value
    # )
    # benchmark_portfolio_current_return = benchmark_portfolio_current_value + cash_flow
    # stock_prices = pd.merge(
    #     stock_prices,
    #     currency_exchange,
    #     "left",
    #     left_on=["date", "stock_ticker"],
    #     right_on=["date", "currency_exchange_rate_ticker"],
    # )
    # stock_portfolio_current_value = 1

    # amount_benchmark_shares = transactions_and_benchmark.groupby("stock_ticker").sum(["value", "equivalent_benchmark_sales_transaction"]).reset_index()
    # amount_benchmark_shares["benchmark_value"] = amount_benchmark_shares["equivalent_benchmark_sales_transaction"] * current_benchmar_value

def _calculate_current_quantity(group):
    group["current_quantity"] = np.nan  # Initialize the new column
    iterator = list(reversed(group.index))

    for i in iterator:
        if i == iterator[0]:
            if np.isnan(group.loc[i, "quantity"]):
                group.loc[i, "current_quantity"] = 0
            else:
                group.loc[i, "current_quantity"] = group.loc[i, "quantity"]
        else:
            if (
                np.isnan(group.loc[i, "quantity"])
                and group.loc[i, "stock_split"] == 0
            ):
                group.loc[i, "current_quantity"] = group.loc[i+1, "current_quantity"]
            elif (
                not np.isnan(group.loc[i, "quantity"])
                and group.loc[i, "stock_split"] == 0
            ):
                group.loc[i, "current_quantity"] = (
                    group.loc[i+1, "current_quantity"] + group.loc[i, "quantity"]
                )
            elif (
                np.isnan(group.loc[i, "quantity"])
                and group.loc[i, "stock_split"] != 0
            ):
                group.loc[i, "current_quantity"] = (
                    group.loc[i+1, "current_quantity"]
                    * group.loc[i, "stock_split"]
                )
            elif (
                not np.isnan(group.loc[i, "quantity"])
                and group.loc[i, "stock_split"] != 0
            ):
                group.loc[i, "current_quantity"] = (
                    group.loc[i+1, "current_quantity"]
                    * group.loc[i, "stock_split"]
                    + group.loc[i, "quantity"]
                )
            else:
                raise NotImplementedError("Scenario not taken into account.")
    group["current_quantity"] = group.apply(
        lambda x: np.nan
        if x["current_quantity"] == 0
        else x["current_quantity"],
        axis=1,
    )
    return group


if __name__ == "__main__":
    preprocess()
