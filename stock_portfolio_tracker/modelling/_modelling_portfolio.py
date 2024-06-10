import pandas as pd
from objetcs import PortfolioData

from . import _utils as utils


def model_portfolio(
    portfolio_data: PortfolioData,
    stock_prices: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    portfolio_model_grouped = pd.merge(
        stock_prices,
        portfolio_data.transactions[["date", "stock_ticker", "quantity", "value"]],
        "left",
        on=["date", "stock_ticker"],
    ).groupby("stock_ticker")
    portfolio_model = pd.concat(
        [
            utils.calculate_current_quantity(group, "quantity")
            for _, group in portfolio_model_grouped
        ],
    )
    portfolio_model = utils.calculate_current_value(
        portfolio_model,
        "current_position_value",
    )

    stock_portfolio_value_evolution = (
        portfolio_model.groupby("date")["current_position_value"]
        .sum()
        .reset_index()
        .rename(columns={"current_position_value": "portfolio_value"})
    )

    stock_portfolio_current_positions = portfolio_model[
        portfolio_model["date"] == portfolio_data.end_date
    ][["date", "stock_ticker", "current_quantity", "current_position_value"]].reset_index(drop=True)
    stock_portfolio_current_positions = (
        stock_portfolio_current_positions.assign(
            percent=round(
                stock_portfolio_current_positions["current_position_value"]
                / stock_portfolio_current_positions["current_position_value"].sum()
                * 100,
                2,
            ),
        )
        .assign(
            current_position_value=round(
                stock_portfolio_current_positions["current_position_value"],
                2,
            ),
        )
        .sort_values(["current_position_value"], ascending=False)
        .reset_index(drop=True)
    )

    return stock_portfolio_value_evolution, stock_portfolio_current_positions
