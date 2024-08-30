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
        on=["date", "ticker_asset"],
    ).groupby("ticker_asset")

    portfolio_model = pd.concat(
        [
            utils.calculate_current_quantity(group, "quantity_asset", "asset")
            for _, group in portfolio_model_grouped
        ],
    )

    portfolio_model = utils.calculate_current_value(
        portfolio_model,
        "asset",
    )

    asset_portfolio_value_evolution = (
        portfolio_model.groupby("date")["current_value_asset"]
        .sum()
        .reset_index()
        .rename(columns={"current_value_asset": "current_value_portfolio"})
        .assign(current_value_portfolio=lambda df: round(df["current_value_portfolio"], 2))
    )

    asset_portfolio_percent_evolution = utils.calculate_current_percent_gain(
        pd.merge(
            asset_portfolio_value_evolution,
            portfolio_data.transactions[["date", "value_asset"]],
            "left",
            on=["date"],
        ),
        "asset",
        "current_value_portfolio",
    )

    asset_portfolio_current_positions = utils.calculat_portfolio_current_positions(
        portfolio_model,
        portfolio_data,
        "asset",
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
