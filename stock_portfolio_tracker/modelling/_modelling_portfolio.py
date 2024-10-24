import pandas as pd

from stock_portfolio_tracker.utils import PortfolioData, sort_at_end

from . import _utils as utils


@sort_at_end()
def model_portfolio(
    portfolio_data: PortfolioData,
    asset_prices: pd.DataFrame,
    sorting_columns: list[dict],  # noqa: ARG001
) -> tuple[pd.DataFrame, pd.DataFrame]:
    portfolio_model_grouped = asset_prices.merge(
        portfolio_data.transactions,
        how="left",
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

    asset_portfolio_percent_evolution = utils.calculate_curr_perc_gain(
        asset_portfolio_value_evolution.merge(
            portfolio_data.transactions[["date", "value_asset"]],
            how="left",
            on=["date"],
        ),
        "asset",
        "current_value_portfolio",
        sorting_columns=[{"columns": ["date"], "ascending": [False]}],
    )

    asset_distribution = utils.calculat_asset_distribution(
        portfolio_model,
        portfolio_data,
        "asset",
    )

    return (
        asset_portfolio_value_evolution,
        asset_portfolio_percent_evolution,
        asset_distribution,
        portfolio_model,
    )
