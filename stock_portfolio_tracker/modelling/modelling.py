"""Calculate all necessary metrics."""

import numpy as np
import pandas as pd
from loguru import logger
from objetcs import PortfolioData


def model_data(
    portfolio_data: PortfolioData,
    benchmarks: pd.DataFrame,
    stock_prices: pd.DataFrame,
) -> list:
    """Calculate all necessary metrics.

    :param portfolio_data: All data of user's portfolio.
    :param benchmarks: Benchmark historical data.
    :param stock_prices: Stock prices historical data.
    :return: Relevant modelled data.
    """
    logger.info("Start of modelling.")

    logger.info("Modelling portfolio.")
    stock_portfolio_value_evolution_grouped = pd.merge(
        stock_prices,
        portfolio_data.transactions[["date", "stock_ticker", "quantity", "value"]],
        "left",
        on=["date", "stock_ticker"],
    ).groupby("stock_ticker")
    stock_portfolio_value_evolution = pd.concat(
        [
            _calculate_current_quantity(group, "quantity")
            for _, group in stock_portfolio_value_evolution_grouped
        ],
    )
    stock_portfolio_value_evolution = _calculate_current_value(
        stock_portfolio_value_evolution,
        "current_position_value",
    )
    stock_portfolio_value_evolution = (
        stock_portfolio_value_evolution.groupby("date")["current_position_value"]
        .sum()
        .reset_index()
        .rename(columns={"current_position_value": "portfolio_value"})
    )

    logger.info("Modelling benchmark.")
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
    benchmark_value_evolution = _calculate_current_value(
        benchmark_value_evolution,
        "benchmark_value",
    )

    logger.info("End of modelling.")

    return stock_portfolio_value_evolution, benchmark_value_evolution


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


def _calculate_current_value(df: pd.DataFrame, current_value_column_name: str) -> pd.DataFrame:
    return (
        df.assign(current_value=df["current_quantity"] * df["open_unadjusted_local_currency"])
        .rename(columns={"current_value": current_value_column_name})
        .groupby(["date", "stock_ticker"])
        .first()  # get the latest current state when there are multiple transactions at the same day for a ticker # noqa: E501
        .sort_values(by=["stock_ticker", "date"], ascending=[True, False])
        .reset_index()
    )
