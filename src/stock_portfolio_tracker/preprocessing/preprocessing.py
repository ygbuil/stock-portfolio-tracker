"""Preprocess input data."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from loguru import logger

from stock_portfolio_tracker import utils
from stock_portfolio_tracker.exceptions import YahooFinanceError
from stock_portfolio_tracker.utils import Config, PortfolioData, sort_at_end

DIR_IN = Path("/workspaces/Stock-Portfolio-Tracker/data/in/")


def preprocess(
    config_file_name: str,
    transactions_file_name: str,
) -> tuple[Config, PortfolioData, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all necessary data from user input and yahoo finance API.

    Args:
        config_file_name: File name for config.
        transactions_file_name: File name for transactions.

    Returns:
        All necessary input data for the calculations.
    """
    config = _load_config(config_file_name)

    portfolio_data = _load_portfolio_data(transactions_file_name)

    currency_exchanges = _load_currency_exchange(
        portfolio_data,
        config.portfolio_currency,
        sorting_columns=[
            {
                "columns": ["ticker_exch_rate", "date"],
                "ascending": [True, False],
            },
        ],
    )

    asset_data = _load_ticker_data(
        list(portfolio_data.assets_info.keys()),
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
        "asset",
        sorting_columns=[{"columns": ["ticker_asset", "date"], "ascending": [True, False]}],
    )
    benchmark_data = _load_ticker_data(
        [config.benchmark_ticker],
        portfolio_data.start_date,
        portfolio_data.end_date,
        currency_exchanges,
        "benchmark",
        sorting_columns=[{"columns": ["ticker_benchmark", "date"], "ascending": [True, False]}],
    )

    logger.info("End of preprocess.")

    return (
        config,
        portfolio_data,
        asset_data[
            [
                "date",
                "ticker_asset",
                "split_asset",
                "close_unadj_local_currency_asset",
            ]
        ],
        asset_data[["date", "ticker_asset", "close_unadj_local_currency_dividends_asset"]],
        benchmark_data[
            [
                "date",
                "ticker_benchmark",
                "split_benchmark",
                "close_unadj_local_currency_benchmark",
            ]
        ],
        benchmark_data[
            ["date", "ticker_benchmark", "close_unadj_local_currency_dividends_benchmark"]
        ],
    )


def _load_config(config_file_name: str) -> Config:
    """Load config.json.

    Args:
        config_file_name: Config file name.

    Returns:
        Config dataclass with the info of config.json.
    """
    with (DIR_IN / Path(config_file_name)).open() as file:
        return Config(**json.load(file))


def _load_portfolio_data(transactions_file_name: str) -> PortfolioData:
    """Load all portfolio data, such as transactions, start date, etc.

    Args:
        transactions_file_name: Transactions file name.

    Returns:
        A class with all portfolio data.
    """
    logger.info("Loading portfolio data.")
    transactions = (
        pd.read_csv(DIR_IN / Path(transactions_file_name))
        .astype(
            {
                "date": str,
                "transaction_type": str,
                "ticker": str,
                "trans_qty": float,
                "trans_val": float,
            },
        )
        .assign(
            date=lambda df: pd.to_datetime(df["date"], format="%d-%m-%Y"),
            trans_val=lambda df: np.where(
                df["transaction_type"] == "Sale",
                abs(df["trans_val"]),
                -abs(df["trans_val"]),
            ),
            trans_qty=lambda df: np.where(
                df["transaction_type"] == "Sale",
                -abs(df["trans_qty"]),
                abs(df["trans_qty"]),
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
                "trans_qty": "trans_qty_asset",
                "trans_val": "trans_val_asset",
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
    """Load currency exchange data from Yahoo Finance.

    Args:
        portfolio_data: Transactions file name.
        local_currency: Portfolio currency.
        sorting_columns: Columns to sort for each returned dataframe.

    Returns:
        Dataframe with the currency exchanges for all assets in the portfolio.

    """
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
                msg = f"""Something went wrong retrieving Yahoo Finance data for
                    ticker {ticker}: {exc}"""
                raise YahooFinanceError(
                    msg,
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

        currency_exchange["ticker_exch_rate"] = origin_currency
        currency_exchanges.append(currency_exchange)

    return pd.concat(currency_exchanges)


@sort_at_end()
def _load_ticker_data(
    tickers: list[str],
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    currency_exchange: pd.DataFrame,
    position_type: str,
    sorting_columns: list[dict],  # noqa: ARG001
) -> pd.DataFrame:
    """Load historical prices and stock splits for all assets in you portfolio, converted to your
    portfolio currency.

    Args:
        tickers: List of tickers to load data for.
        start_date: Start date to load the data.
        end_date: End date to load the data.
        currency_exchange: Dataframe with the currency exchanges for all assets to be loaded.
        position_type: Type of position (asset, benchmark, etc).
        sorting_columns: Columns to sort for each returned dataframe.

    Returns:
        Dataframe with all historical prices and stock splits.
    """
    asset_data = utils.multithreader(
        _load_prices_and_dividends, [(ticker, start_date, end_date) for ticker in tickers]
    )

    asset_data = pd.concat(asset_data).merge(
        currency_exchange,
        "left",
        left_on=["date", "origin_currency"],
        right_on=["date", "ticker_exch_rate"],
    )

    asset_data = _convert_to_local_currency(
        asset_data,
        "close_unadj_origin_currency",
        f"close_unadj_local_currency_{position_type}",
    )

    asset_data = _convert_to_local_currency(
        asset_data,
        "close_unadj_origin_currency_dividends",
        f"close_unadj_local_currency_dividends_{position_type}",
    )

    return asset_data.rename(
        columns={
            "ticker": f"ticker_{position_type}",
            "split": f"split_{position_type}",
        },
    )[
        [
            "date",
            f"ticker_{position_type}",
            f"split_{position_type}",
            f"close_unadj_local_currency_{position_type}",
            f"close_unadj_local_currency_dividends_{position_type}",
        ]
    ]


def _load_prices_and_dividends(
    ticker: str,
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
) -> pd.DataFrame:
    """Load the following daily data at market close for a given ticker:
        - Unadjusted asset price.
        - Stock splits.
        - Dividends (at Ex-Dividend Date).

    Args:
        ticker: Asset ticker
        start_date: Start date to load the data.
        end_date: End date to load the data.

    Raises:
        YahooFinanceError: Something went wrong with the Yahoo Finance API.

    Returns:
        Dataframe with the historical asset price and stock splits.
    """
    logger.info(f"Loading historical data for {ticker}")
    try:
        asset = yf.Ticker(ticker)
        asset_data = (
            asset.history(start=start_date)[["Close", "Stock Splits", "Dividends"]]
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
    except Exception as exc:
        msg = f"Something went wrong retrieving Yahoo Finance data for ticker {ticker}: {exc}"
        raise YahooFinanceError(
            msg,
        ) from exc

    asset_data = _convert_to_unadj(start_date, end_date, asset_data).assign(
        origin_currency=asset.info.get("currency"),
        ticker=ticker,
    )

    return asset_data[
        [
            "date",
            "ticker",
            "close_unadj_origin_currency",
            "close_unadj_origin_currency_dividends",
            "origin_currency",
            "split",
        ]
    ]


def _convert_to_unadj(
    start_date: pd.Timestamp,
    end_date: pd.Timestamp,
    asset_data: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate unadjusted stock price and dividends.

    Yahoo finance reports the split the day that the split already takes place:
    Example: NVDA traded at (aprox) 1000/share at 2024-06-09, and at 2024-06-10 at
    market open it was trading at 100/share due to the split. Yahoo reported a 10
    stock_split for at date 2024-06-10.

    Args:
        start_date: Start date to load the data.
        end_date: End date to load the data.
        asset_data: Asset price, dividends and splits.

    Returns:
        Adjusted price and dividends.
    """
    return (
        pd.DataFrame(
            {"date": reversed(pd.date_range(start=start_date, end=end_date, freq="D"))},
        )
        .merge(
            asset_data,
            "left",
            on="date",
        )
        .assign(
            split=lambda df: df["split"].fillna(1).replace(0, 1),
            close_adj_origin_currency=lambda df: df["close_adj_origin_currency"].bfill().ffill(),
            close_adj_origin_currency_dividends=lambda df: df[
                "close_adj_origin_currency_dividends"
            ].fillna(0),
            split_cumsum=lambda df: df["split"].cumprod().shift(1).fillna(1),
            close_unadj_origin_currency=lambda df: df["close_adj_origin_currency"]
            * df["split_cumsum"],
            close_unadj_origin_currency_dividends=lambda df: df[
                "close_adj_origin_currency_dividends"
            ]
            * df["split_cumsum"],
        )
    )


def _convert_to_local_currency(
    df: pd.DataFrame,
    origin_curr_col_name: str,
    local_curr_col_name: str,
) -> pd.DataFrame:
    """Convert origin to local currency for the specified column.

    Args:
        df: Dataframe to convert.
        origin_curr_col_name: Name of the column with origin currency to convert.
        local_curr_col_name: Name of the column with the converted currency.

    Returns:
        Datframe with the currency in local price.
    """
    return df.assign(
        **{
            local_curr_col_name: lambda df: df[origin_curr_col_name] / df["close_currency_rate"],
        },
    )
