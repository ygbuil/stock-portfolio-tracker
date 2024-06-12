import pandas as pd
from objetcs import PortfolioData

from . import _utils as utils


def model_portfolio(
    portfolio_data: PortfolioData,
    asset_prices: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    portfolio_model_grouped = pd.merge(
        asset_prices,
        portfolio_data.transactions[["date", "asset_ticker", "quantity", "value"]],
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
            portfolio_data.transactions,
            "left",
            on=["date"],
        ),
        "portfolio_value",
    )

    asset_portfolio_current_positions = portfolio_model[
        portfolio_model["date"] == portfolio_data.end_date
    ][["date", "asset_ticker", "current_quantity", "current_position_value"]].reset_index(drop=True)
    asset_portfolio_current_positions = (
        asset_portfolio_current_positions.assign(
            percent=round(
                asset_portfolio_current_positions["current_position_value"]
                / asset_portfolio_current_positions["current_position_value"].sum()
                * 100,
                2,
            ),
            current_position_value=round(
                asset_portfolio_current_positions["current_position_value"],
                2,
            ),
        )
        .sort_values(["current_position_value"], ascending=False)
        .reset_index(drop=True)
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
    )
