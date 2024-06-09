import pandas as pd
from objetcs import PortfolioData

from . import _utils as utils


def model_portfolio(portfolio_data: PortfolioData, stock_prices: pd.DataFrame) -> pd.DataFrame:
    stock_portfolio_value_evolution_grouped = pd.merge(
        stock_prices,
        portfolio_data.transactions[["date", "stock_ticker", "quantity", "value"]],
        "left",
        on=["date", "stock_ticker"],
    ).groupby("stock_ticker")
    stock_portfolio_value_evolution = pd.concat(
        [
            utils.calculate_current_quantity(group, "quantity")
            for _, group in stock_portfolio_value_evolution_grouped
        ],
    )
    stock_portfolio_value_evolution = utils.calculate_current_value(
        stock_portfolio_value_evolution,
        "current_position_value",
    )

    return (
        stock_portfolio_value_evolution.groupby("date")["current_position_value"]
        .sum()
        .reset_index()
        .rename(columns={"current_position_value": "portfolio_value"})
    )
