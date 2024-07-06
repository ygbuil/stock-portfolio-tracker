import pandas as pd

from stock_portfolio_tracker.objetcs import PortfolioData

from . import _utils as utils


def model_portfolio(
    portfolio_data: PortfolioData,
    asset_prices: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    portfolio_model_grouped = pd.merge(
        asset_prices,
        portfolio_data.transactions,
        "left",
        on=["date", "asset_ticker"],
    ).groupby("asset_ticker")

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

    asset_portfolio_value_evolution = (
        portfolio_model.groupby("date")["current_position_value"]
        .sum()
        .reset_index()
        .rename(columns={"current_position_value": "portfolio_value"})
        .assign(portfolio_value=lambda df: round(df["portfolio_value"], 2))
    )

    asset_portfolio_percent_evolution = utils.calculate_current_percent_gain(
        pd.merge(
            asset_portfolio_value_evolution,
            portfolio_data.transactions[["date", "value"]],
            "left",
            on=["date"],
        ),
        "portfolio_value",
    )

    asset_portfolio_current_positions = utils.calculat_portfolio_current_positions(
        portfolio_model,
        portfolio_data,
    )

    return (
        utils.sort_by_columns(
            asset_portfolio_value_evolution,
            ["date"],
            [False],
        ),
        utils.sort_by_columns(
            asset_portfolio_percent_evolution,
            ["date"],
            [False],
        ),
        utils.sort_by_columns(
            asset_portfolio_current_positions,
            ["current_position_value"],
            [False],
        ),
        utils.sort_by_columns(
            portfolio_model,
            ["date"],
            [False],
        ),
    )
