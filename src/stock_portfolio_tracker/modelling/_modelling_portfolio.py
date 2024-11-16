import pandas as pd

from stock_portfolio_tracker.utils import PortfolioData, sort_at_end

from . import _utils as utils


@sort_at_end()
def model_portfolio(
    portfolio_data: PortfolioData,
    asset_prices: pd.DataFrame,
    sorting_columns: list[dict],  # noqa: ARG001
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Caclulates the following metrics for the assets:
    - For the overall portfolio, on a daily basis:
        - Value of the portfolio.
        - Absoulte gain since start.
        - Percentage gain since start.
    - For each asset, on a daily basis:
        - Value of the asset.
        - Quantity of the asset.
    - Asset distribution (in value and percentage) as of latest date.

    :param portfolio_data: Transactions history and other portfolio data.
    :param asset_prices: Daily prices of each asset as of Yahoo Finance.
    :param sorting_columns: Columns to sort for each returned dataframe.
    :return: Portfolio metrics, individual asset metrics and asset ditribution.
    """
    portfolio_model = pd.concat(
        [
            utils.calc_curr_qty(group, "asset")
            for _, group in (
                asset_prices.merge(
                    portfolio_data.transactions,
                    how="left",
                    on=["date", "ticker_asset"],
                ).groupby("ticker_asset")
            )
        ],
    )

    portfolio_model = utils.calc_curr_val(
        portfolio_model,
        "asset",
    )

    portfolio_val_evolution = (
        portfolio_model.groupby("date")["curr_val_asset"]
        .sum()
        .reset_index()
        .rename(columns={"curr_val_asset": "curr_val_portfolio"})
        .assign(curr_val_portfolio=lambda df: round(df["curr_val_portfolio"], 2))
    )

    portfolio_perc_evolution = utils.calc_curr_perc_gain(
        portfolio_val_evolution.merge(
            portfolio_data.transactions[["date", "trans_val_asset"]],
            how="left",
            on=["date"],
        ).rename(columns={"trans_val_asset": "trans_val_portfolio"}),
        "portfolio",
        sorting_columns=[{"columns": ["date"], "ascending": [False]}],
    )

    assets_distribution = utils.calc_assets_distribution(
        portfolio_model,
        portfolio_data,
        "asset",
    )

    return (
        portfolio_val_evolution.merge(
            portfolio_perc_evolution,
            how="left",
            on=["date"],
        ),
        assets_distribution,
        portfolio_model,
    )
