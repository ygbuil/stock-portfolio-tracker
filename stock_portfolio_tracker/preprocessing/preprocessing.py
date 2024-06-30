"""Preprocess input data."""

import json
import os
from pathlib import Path
from typing import Callable

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from loguru import logger

from stock_portfolio_tracker.objetcs import Config, PortfolioData


def preprocess() -> tuple[Config, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all necessary data from user input and yahoo finance API.

    :return: All necessary input data for the calculations.
    """
    logger.info("Start of preprocess.")

    config_file_name, transactions_file_name = _get_input_files_names()

    config = _load_config(config_file_name)

    portfolio_data = _load_portfolio_data(transactions_file_name)

    currency_exchanges = _load_currency_exchange(
        portfolio_data,
        config.portfolio_currency,
    )

    asset_prices = _load_assets_prices(
        portfolio_data.assets_info.keys(),
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
    )
    benchmarks = _load_assets_prices(
        config.benchmark_tickers,
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
    )

    logger.info("End of preprocess.")

    return config, portfolio_data, asset_prices, benchmarks


def _sort_at_end(ticker_column: str, date_column: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        def wrapper(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
            df = func(df, *args, **kwargs)
            return df.sort_values(
                by=[ticker_column, date_column],
                ascending=[True, False],
            ).reset_index(drop=True)

        return wrapper

    return decorator


def _get_input_files_names() -> tuple[str, str]:
    load_dotenv()
    config_file_name = os.getenv("CONFIG_NAME")
    transactions_file_name = os.getenv("TRANSACTIONS_NAME")

    if not config_file_name:
        config_file_name = "config.json"

    if not transactions_file_name:
        transactions_file_name = "transactions.csv"

    return config_file_name, transactions_file_name


def _load_config(config_file_name: str) -> Config:
    with Path(f"/workspaces/Stock-Portfolio-Tracker/data/in/{config_file_name}").open() as file:
        return Config(**json.load(file))


def _load_portfolio_data(transactions_file_name: str) -> PortfolioData:
    logger.info("Loading portfolio data.")
    transactions = (
        pd.read_csv(
            Path(f"/workspaces/Stock-Portfolio-Tracker/data/in/{transactions_file_name}"),
        )
        .astype(
            {
                "date": str,
                "transaction_type": str,
                "asset_ticker": str,
                "quantity": float,
                "value": float,
            },
        )
        .assign(
            date=lambda df: pd.to_datetime(df["date"], format="%d-%m-%Y"),
            value=lambda df: df.apply(
                lambda x: abs(x["value"]) if x["transaction_type"] == "Sale" else -abs(x["value"]),
                axis=1,
            ),
            quantity=lambda df: df.apply(
                lambda x: -abs(x["quantity"])
                if x["transaction_type"] == "Sale"
                else abs(x["quantity"]),
                axis=1,
            ),
        )
        .drop("transaction_type", axis=1)
        .sort_values(
            by=["date", "asset_ticker"],
            ascending=[False, True],
        )
        .reset_index(drop=True)
    )

    assets_info = {}

    for ticker in sorted(transactions["asset_ticker"].unique()):
        asset = yf.Ticker(ticker)
        assets_info[ticker] = {
            "name": asset.info.get("shortName"),
            "currency": asset.info.get("currency"),
        }

    return PortfolioData(
        transactions=transactions,
        assets_info=assets_info,
        start_date=min(transactions["date"]),
        end_date=pd.Timestamp.today().normalize() - pd.Timedelta(days=1),
    )


@_sort_at_end("currency_exchange_rate_ticker", "date")
def _load_currency_exchange(portfolio_data: PortfolioData, local_currency: str) -> pd.DataFrame:
    currency_exchanges = []
    portfolio_currencies = {item[1]["currency"] for item in portfolio_data.assets_info.items()} | {
        local_currency,
    }
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

    for origin_currency in portfolio_currencies:
        ticker = f"{local_currency}{origin_currency}=X"
        logger.info(f"Loading currency exchange for {ticker}.")

        if origin_currency != local_currency:
            try:
                currency_exchange = (
                    yf.Ticker(ticker)
                    .history(start=portfolio_data.start_date, end=portfolio_data.end_date)[
                        ["Close"]
                    ]
                    .sort_index(ascending=False)
                    .reset_index()
                    .rename(columns={"Close": "close_currency_rate", "Date": "date"})
                    .assign(date=lambda df: pd.to_datetime(df["date"].dt.strftime("%Y-%m-%d")))
                )
            except Exception as exc:
                raise Exception(
                    f"""Something went wrong retrieving Yahoo Finance data for
                    ticker {ticker}: {exc}""",
                ) from exc

            currency_exchange = pd.merge(
                full_date_range,
                currency_exchange,
                "left",
                on="date",
            ).assign(
                close_currency_rate=lambda df: df["close_currency_rate"].bfill().ffill(),
            )
        else:
            currency_exchange = full_date_range.assign(close_currency_rate=1)

        currency_exchange["currency_exchange_rate_ticker"] = origin_currency
        currency_exchanges.append(currency_exchange)

    return pd.concat(currency_exchanges)


@_sort_at_end("asset_ticker", "date")
def _load_assets_prices(
    tickers: list[str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    currency_exchange: pd.DataFrame,
) -> pd.DataFrame:
    asset_prices = []

    for ticker in tickers:
        logger.info(f"Loading historical asset prices for {ticker}")
        asset_price = _load_ticker_data(ticker, start_date, end_date)
        asset_prices.append(asset_price)

    # convert to local currency
    return pd.merge(
        pd.concat(asset_prices),
        currency_exchange,
        "left",
        left_on=["date", "origin_currency"],
        right_on=["date", "currency_exchange_rate_ticker"],
    ).assign(
        close_unadjusted_local_currency=lambda df: df.apply(
            lambda x: x["close_unadjusted_origin_currency"] / x["close_currency_rate"],
            axis=1,
        ),
    )[["date", "asset_ticker", "close_unadjusted_local_currency", "asset_split"]]


def _load_ticker_data(
    ticker: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    try:
        asset = yf.Ticker(ticker)
        asset_price = (
            asset.history(start=start_date, end=end_date)[["Close", "Stock Splits"]]
            .sort_index(ascending=False)
            .reset_index()
            .rename(
                columns={
                    "Close": "close_adjusted_origin_currency",
                    "Date": "date",
                    "Stock Splits": "asset_split",
                },
            )
            .assign(date=lambda df: pd.to_datetime(df["date"].dt.strftime("%Y-%m-%d")))
        )
    except Exception as exc:
        raise Exception(
            f"Something went wrong retrieving Yahoo Finance data for ticker {ticker}: {exc}",
        ) from exc

    # calculate unadjusted stock price
    # NOTE: yahoo finance reports the split the day that the split already takes place:
    # Example: NVDA traded at (aprox) 1000/share at 2024-06-09, and at 2024-06-10 at
    # market open it was trading at 100/share due to the split. Yahoo reported a 10
    # stock_split for at date 2024-06-10.
    return (
        pd.merge(
            pd.DataFrame(
                {"date": reversed(pd.date_range(start=start_date, end=end_date, freq="D"))},
            ),
            asset_price,
            "left",
            on="date",
        ).assign(
            asset_split=lambda df: df["asset_split"].fillna(0),
            close_adjusted_origin_currency=lambda df: df["close_adjusted_origin_currency"]
            .bfill()
            .ffill(),
            asset_split_cumsum=lambda df: df["asset_split"]
            .replace(0, 1)
            .cumprod()
            .shift(1)
            .fillna(1),
            close_unadjusted_origin_currency=lambda df: df.apply(
                lambda x: x["close_adjusted_origin_currency"] * x["asset_split_cumsum"],
                axis=1,
            ),
            origin_currency=asset.info.get("currency"),
            asset_ticker=ticker,
        )
    )[
        [
            "date",
            "asset_ticker",
            "close_unadjusted_origin_currency",
            "origin_currency",
            "asset_split",
        ]
    ]
