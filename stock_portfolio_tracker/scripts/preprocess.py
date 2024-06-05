"""Preprocess."""

import os
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class PortfolioData:
    """Portfolio data."""

    transactions: pd.DataFrame
    tickers: list[str]
    currencies: list[str]
    start_date: pd.Timestamp
    end_date: pd.Timestamp


def preprocess() -> None:
    """Preprocess."""
    portfolio_data = _load_portfolio_data()

    currency_exchanges = _load_currency_exchange(
        portfolio_data,
        "EUR",
    )

    stock_prices = _load_portfolio_stocks_historical_prices(
        portfolio_data.tickers,
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
    )
    benchmarks = _load_portfolio_stocks_historical_prices(
        ["SXR8.DE"],
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
    )

    _get_performance(portfolio_data, benchmarks, stock_prices)


def _load_portfolio_data() -> PortfolioData:
    transactions = pd.read_csv(
        Path(os.path.dirname(os.path.realpath(__file__))) / Path("../data/in/transactions.csv"),  # noqa: PTH120
    ).astype(
        {
            "date": str,
            "transaction_type": str,
            "stock_name": str,
            "stock_ticker": str,
            "origin_currency": str,
            "quantity": float,
            "value": float,
        },
    )

    transactions["date"] = pd.to_datetime(transactions["date"], dayfirst=True)
    transactions["value"] = transactions.apply(
        lambda x: abs(x["value"]) if x["transaction_type"] == "Sale" else -abs(x["value"]),
        axis=1,
    )
    transactions["quantity"] = transactions.apply(
        lambda x: -abs(x["quantity"]) if x["transaction_type"] == "Sale" else abs(x["quantity"]),
        axis=1,
    )
    transactions = transactions.drop("transaction_type", axis=1)

    # TODO: think what to do with this field
    transactions = transactions.drop("stock_name", axis=1)

    return PortfolioData(
        transactions=transactions,
        tickers=transactions["stock_ticker"].unique(),
        currencies=transactions["origin_currency"].unique(),
        start_date=min(transactions["date"]),
        end_date=pd.Timestamp.today(),
    )


def _load_portfolio_stocks_historical_prices(
    tickers: list[str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    currency_exchange: pd.DataFrame,
) -> pd.DataFrame:
    stock_prices = []

    for ticker in tickers:
        stock_price = _load_ticker_data(ticker, start_date, end_date)
        stock_price["stock_ticker"] = ticker
        stock_prices.append(stock_price)

    stock_prices = pd.concat(stock_prices)

    return _convert_price_to_local_currency(stock_prices, currency_exchange)


def _convert_price_to_local_currency(
    stock_prices: pd.DataFrame,
    currency_exchange: pd.DataFrame,
) -> pd.DataFrame:
    stock_prices = pd.merge(
        stock_prices,
        currency_exchange,
        "left",
        left_on=["date", "origin_currency"],
        right_on=["date", "currency_exchange_rate_ticker"],
    )
    stock_prices["open_unadjusted_local_currency"] = (
        stock_prices["open_unadjusted_origin_currency"] / stock_prices["open_currency_rate"]
    )
    return stock_prices[["date", "stock_ticker", "open_unadjusted_local_currency", "stock_split"]]


def _load_ticker_data(
    ticker: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    stock = yf.Ticker(ticker)
    stock_price = (
        stock.history(start=start_date, end=end_date)[["Open", "Stock Splits"]]
        .sort_index(ascending=False)
        .reset_index()
        .rename(
            columns={
                "Open": "open_adjusted_origin_currency",
                "Date": "date",
                "Stock Splits": "stock_split",
            },
        )
    )

    stock_price["date"] = (
        stock_price["date"].dt.strftime("%Y-%m-%d").apply(lambda x: pd.Timestamp(x))
    )

    # fill missing dates
    full_date_range = pd.DataFrame(
        {"date": reversed(pd.date_range(start=start_date, end=end_date, freq="D"))},
    )
    stock_price = pd.merge(full_date_range, stock_price, "left", on="date")
    stock_price["stock_split"] = stock_price["stock_split"].fillna(0)
    stock_price["open_adjusted_origin_currency"] = (
        stock_price["open_adjusted_origin_currency"].bfill().ffill()
    )

    # calculate stock splits
    stock_price["stock_split_cumsum"] = stock_price["stock_split"].replace(0, 1).cumprod()
    stock_price["open_unadjusted_origin_currency"] = (
        stock_price["open_adjusted_origin_currency"] * stock_price["stock_split_cumsum"]
    )

    # add currency
    stock_price["origin_currency"] = stock.info.get("currency")

    return stock_price[
        ["date", "open_unadjusted_origin_currency", "origin_currency", "stock_split"]
    ]


def _load_currency_exchange(portfolio_data: PortfolioData, local_currency: str) -> pd.DataFrame:
    currency_exchanges = []

    for origin_currency in portfolio_data.currencies:
        if origin_currency != local_currency:
            currency_exchange = (
                yf.Ticker(f"{local_currency}{origin_currency}=X")
                .history(start=portfolio_data.start_date, end=portfolio_data.end_date)[["Open"]]
                .sort_index(ascending=False)
                .reset_index()
                .rename(columns={"Open": "open_currency_rate", "Date": "date"})
            )
            currency_exchange["date"] = (
                currency_exchange["date"].dt.strftime("%Y-%m-%d").apply(lambda x: pd.Timestamp(x))
            )
            full_date_range = pd.DataFrame(
                {
                    "date": reversed(
                        pd.date_range(
                            start=portfolio_data.start_date,
                            end=portfolio_data.end_date,
                            freq="D",
                        ),
                    ),
                },
            )
            currency_exchange = pd.merge(
                full_date_range,
                currency_exchange,
                "left",
                on="date",
            )
            currency_exchange["open_currency_rate"] = (
                currency_exchange["open_currency_rate"].bfill().ffill()
            )
        else:
            currency_exchange = pd.DataFrame(
                {
                    "date": reversed(
                        pd.date_range(
                            start=portfolio_data.start_date,
                            end=portfolio_data.end_date,
                        ),
                    ),
                    "open_currency_rate": 1,
                },
            )

        currency_exchange["currency_exchange_rate_ticker"] = origin_currency
        currency_exchanges.append(currency_exchange)

    return pd.concat(currency_exchanges).reset_index(drop=True)


def _get_performance(
    portfolio_data: PortfolioData,
    benchmarks: pd.DataFrame,
    stock_prices: pd.DataFrame,
) -> None:
    stock_portfolio_value_evolution = pd.merge(
        stock_prices,
        portfolio_data.transactions[["date", "stock_ticker", "quantity", "value"]],
        "left",
        on=["date", "stock_ticker"],
    )
    grouped = stock_portfolio_value_evolution.reset_index(drop=True).groupby(
        "stock_ticker",
    )
    stock_portfolio_value_evolution = []
    for _, group in grouped:
        stock_portfolio_value_evolution.append(
            _calculate_current_quantity(group, "quantity"),
        )
    stock_portfolio_value_evolution = pd.concat(stock_portfolio_value_evolution)
    stock_portfolio_value_evolution["portfolio_value"] = (
        stock_portfolio_value_evolution["current_quantity"]
        * stock_portfolio_value_evolution["open_unadjusted_local_currency"]
    )
    # TODO: groupby("date").mean() per ticker i groupby sum
    stock_portfolio_value_evolution = (
        stock_portfolio_value_evolution.groupby("date")["portfolio_value"].sum().reset_index()
    )

    benchmark_value_evolution = pd.merge(
        benchmarks,
        portfolio_data.transactions[["date", "quantity", "value"]],
        "left",
        on=["date"],
    )
    benchmark_value_evolution["benchmark_quantity"] = (
        -benchmark_value_evolution["value"]
        / benchmark_value_evolution["open_unadjusted_local_currency"]
    )
    benchmark_value_evolution = _calculate_current_quantity(
        benchmark_value_evolution,
        "benchmark_quantity",
    )
    benchmark_value_evolution["benchmark_value"] = (
        benchmark_value_evolution["current_quantity"]
        * benchmark_value_evolution["open_unadjusted_local_currency"]
    )
    benchmark_value_evolution = (
        benchmark_value_evolution.groupby("date")["benchmark_value"].mean().reset_index()
    )

    plt.figure(figsize=(10, 6))
    plt.plot(
        stock_portfolio_value_evolution["date"],
        stock_portfolio_value_evolution["portfolio_value"],
        linestyle="-",
        color="blue",
        label="Portfolio value",
    )
    plt.plot(
        benchmark_value_evolution["date"],
        benchmark_value_evolution["benchmark_value"],
        linestyle="-",
        color="orange",
        label="Benchmark value",
    )
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.title("Value Over Time")
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plot_filename = Path("stock_portfolio_tracker/data/out/plot.png")
    plt.savefig(plot_filename)
    plt.close()


def _calculate_current_quantity(group: pd.DataFrame, quantity_col_name: str) -> pd.DataFrame:
    group["current_quantity"] = np.nan  # Initialize the new column
    iterator = list(reversed(group.index))

    for i in iterator:
        if i == iterator[0]:
            if np.isnan(group.loc[i, quantity_col_name]):
                group.loc[i, "current_quantity"] = 0
            else:
                group.loc[i, "current_quantity"] = group.loc[i, quantity_col_name]
        elif np.isnan(group.loc[i, quantity_col_name]) and group.loc[i, "stock_split"] == 0:
            group.loc[i, "current_quantity"] = group.loc[i + 1, "current_quantity"]
        elif not np.isnan(group.loc[i, quantity_col_name]) and group.loc[i, "stock_split"] == 0:
            group.loc[i, "current_quantity"] = (
                group.loc[i + 1, "current_quantity"] + group.loc[i, quantity_col_name]
            )
        elif np.isnan(group.loc[i, quantity_col_name]) and group.loc[i, "stock_split"] != 0:
            group.loc[i, "current_quantity"] = (
                group.loc[i + 1, "current_quantity"] * group.loc[i, "stock_split"]
            )
        elif not np.isnan(group.loc[i, quantity_col_name]) and group.loc[i, "stock_split"] != 0:
            group.loc[i, "current_quantity"] = (
                group.loc[i + 1, "current_quantity"] * group.loc[i, "stock_split"]
                + group.loc[i, quantity_col_name]
            )
        else:
            raise NotImplementedError("Scenario not taken into account.")
    group["current_quantity"] = group.apply(
        lambda x: np.nan if x["current_quantity"] == 0 else x["current_quantity"],
        axis=1,
    )
    return group


if __name__ == "__main__":
    preprocess()
