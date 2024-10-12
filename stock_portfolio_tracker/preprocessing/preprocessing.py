"""Preprocess input data."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from stock_portfolio_tracker.utils import Config, PortfolioData, sort_at_end


def preprocess(
    config_file_name: str,
    transactions_file_name: str,
) -> tuple[Config, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all necessary data from user input and yahoo finance API.

    :param config_file_name: File name for config.
    :param transactions_file_name: File name for transactions.
    :return: All necessary input data for the calculations.
    """
    config = _load_config(config_file_name)

    portfolio_data = _load_portfolio_data(transactions_file_name)

    currency_exchanges = _load_currency_exchange(
        portfolio_data,
        config.portfolio_currency,
        sorting_columns=[
            {
                "columns": ["currency_exchange_rate_ticker", "date"],
                "ascending": [True, False],
            },
        ],
    )

    asset_prices = _load_prices(
        portfolio_data.assets_info.keys(),
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
        "asset",
        sorting_columns=[{"columns": ["ticker_asset", "date"], "ascending": [True, False]}],
    )
    benchmarks = _load_prices(
        config.benchmark_tickers,
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
        "benchmark",
        sorting_columns=[{"columns": ["ticker_benchmark", "date"], "ascending": [True, False]}],
    )

    logger.info("End of preprocess.")

    return config, portfolio_data, asset_prices, benchmarks


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
                "ticker": str,
                "quantity": float,
                "value": float,
            },
        )
        .assign(
            date=lambda df: pd.to_datetime(df["date"], format="%d-%m-%Y"),
            value=lambda df: np.where(
                df["transaction_type"] == "Sale",
                abs(df["value"]),
                -abs(df["value"]),
            ),
            quantity=lambda df: np.where(
                df["transaction_type"] == "Sale",
                -abs(df["quantity"]),
                abs(df["quantity"]),
            ),
        )
        .drop("transaction_type", axis=1)
        .sort_values(
            by=["date", "ticker"],
            ascending=[False, True],
        )
        .rename(
            columns={
                "ticker": "ticker_asset",
                "quantity": "quantity_asset",
                "value": "value_asset",
            },
        )
        .reset_index(drop=True)
    )

    assets_info = {}

    for ticker in sorted(transactions["ticker_asset"].unique()):
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


@sort_at_end()
def _load_currency_exchange(
    portfolio_data: PortfolioData,
    local_currency: str,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
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
                    .history(start=portfolio_data.start_date)[["Close"]]
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

            currency_exchange = full_date_range.merge(
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


@sort_at_end()
def _load_prices(
    tickers: list[str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    currency_exchange: pd.DataFrame,
    position_type: str,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
    asset_prices = []

    for ticker in tickers:
        logger.info(f"Loading historical asset prices for {ticker}")
        asset_price = _load_ticker_data(ticker, start_date, end_date)
        asset_prices.append(asset_price)

    # convert to local currency
    return (
        pd.concat(asset_prices)
        .merge(
            currency_exchange,
            "left",
            left_on=["date", "origin_currency"],
            right_on=["date", "currency_exchange_rate_ticker"],
        )
        .assign(
            **{
                f"close_unadjusted_local_currency_{position_type}": lambda df: df[
                    "close_unadjusted_origin_currency"
                ]
                / df["close_currency_rate"],
            },
        )
        .rename(
            columns={
                "ticker": f"ticker_{position_type}",
                "split": f"split_{position_type}",
            },
        )[
            [
                "date",
                f"ticker_{position_type}",
                f"split_{position_type}",
                f"close_unadjusted_local_currency_{position_type}",
            ]
        ]
    )


def _load_ticker_data(
    ticker: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    try:
        asset = yf.Ticker(ticker)
        asset_price = (
            asset.history(start=start_date)[["Close", "Stock Splits"]]
            .sort_index(ascending=False)
            .reset_index()
            .rename(
                columns={
                    "Close": "close_adjusted_origin_currency",
                    "Date": "date",
                    "Stock Splits": "split",
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
        pd.DataFrame(
            {"date": reversed(pd.date_range(start=start_date, end=end_date, freq="D"))},
        )
        .merge(
            asset_price,
            "left",
            on="date",
        )
        .assign(
            split=lambda df: df["split"].fillna(0),
            close_adjusted_origin_currency=lambda df: df["close_adjusted_origin_currency"]
            .bfill()
            .ffill(),
            split_cumsum=lambda df: df["split"].replace(0, 1).cumprod().shift(1).fillna(1),
            close_unadjusted_origin_currency=lambda df: df["close_adjusted_origin_currency"]
            * df["split_cumsum"],
            origin_currency=asset.info.get("currency"),
            ticker=ticker,
        )
    )[
        [
            "date",
            "ticker",
            "close_unadjusted_origin_currency",
            "origin_currency",
            "split",
        ]
    ]
