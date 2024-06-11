"""Preprocess input data."""

import json
import os
from pathlib import Path
from typing import Callable

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from loguru import logger
from objetcs import Config, PortfolioData


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

    asset_prices = _load_portfolio_assets_historical_prices(
        portfolio_data.assets_info.keys(),
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
    )
    benchmarks = _load_portfolio_assets_historical_prices(
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
            date=lambda df: df.apply(
                lambda x: pd.to_datetime(x["date"], dayfirst=True),
                axis=1,
            ),
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
        end_date=pd.Timestamp.today().normalize(),
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
                    .history(start=portfolio_data.start_date, end=portfolio_data.end_date)[["Open"]]
                    .sort_index(ascending=False)
                    .reset_index()
                    .rename(columns={"Open": "open_currency_rate", "Date": "date"})
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
            )
            currency_exchange = currency_exchange.assign(
                open_currency_rate=currency_exchange["open_currency_rate"].bfill().ffill(),
            )
        else:
            currency_exchange = full_date_range.assign(open_currency_rate=1)

        currency_exchange["currency_exchange_rate_ticker"] = origin_currency
        currency_exchanges.append(currency_exchange)

    return pd.concat(currency_exchanges)


@_sort_at_end("asset_ticker", "date")
def _load_portfolio_assets_historical_prices(
    tickers: list[str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    currency_exchange: pd.DataFrame,
) -> pd.DataFrame:
    asset_prices = []

    for ticker in tickers:
        logger.info(f"Loading historical asset prices for {ticker}")
        asset_price = _load_ticker_data(ticker, start_date, end_date)
        asset_price["asset_ticker"] = ticker
        asset_prices.append(asset_price)

    asset_prices = pd.concat(asset_prices)

    return _convert_price_to_local_currency(asset_prices, currency_exchange)


def _convert_price_to_local_currency(
    asset_prices: pd.DataFrame,
    currency_exchange: pd.DataFrame,
) -> pd.DataFrame:
    asset_prices = pd.merge(
        asset_prices,
        currency_exchange,
        "left",
        left_on=["date", "origin_currency"],
        right_on=["date", "currency_exchange_rate_ticker"],
    )
    asset_prices["open_unadjusted_local_currency"] = (
        asset_prices["open_unadjusted_origin_currency"] / asset_prices["open_currency_rate"]
    )
    return asset_prices[["date", "asset_ticker", "open_unadjusted_local_currency", "asset_split"]]


def _load_ticker_data(
    ticker: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    try:
        asset = yf.Ticker(ticker)
        asset_price = (
            asset.history(start=start_date)[["Open", "Stock Splits"]]
            .sort_index(ascending=False)
            .reset_index()
            .rename(
                columns={
                    "Open": "open_adjusted_origin_currency",
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

    # fill missing dates
    full_date_range = pd.DataFrame(
        {"date": reversed(pd.date_range(start=start_date, end=end_date, freq="D"))},
    )
    asset_price = pd.merge(full_date_range, asset_price, "left", on="date")
    asset_price["asset_split"] = asset_price["asset_split"].fillna(0)
    asset_price["open_adjusted_origin_currency"] = (
        asset_price["open_adjusted_origin_currency"].bfill().ffill()
    )

    # calculate asset splits
    asset_price["asset_split_cumsum"] = (
        asset_price["asset_split"].replace(0, 1).cumprod().shift(1).fillna(1)
    )
    asset_price["open_unadjusted_origin_currency"] = (
        asset_price["open_adjusted_origin_currency"] * asset_price["asset_split_cumsum"]
    )

    # add currency
    asset_price["origin_currency"] = asset.info.get("currency")

    return asset_price[
        ["date", "open_unadjusted_origin_currency", "origin_currency", "asset_split"]
    ]
