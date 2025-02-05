import pandas as pd

from stock_portfolio_tracker.exceptions import UnsortedError
from stock_portfolio_tracker.utils import PortfolioData, sort_at_end

from . import _utils as utils


@sort_at_end()
def model_portfolio(
    portfolio_data: PortfolioData,
    asset_prices: pd.DataFrame,
    asset_dividends: pd.DataFrame,
    sorting_columns: list[dict[str, list[str | bool]]],  # noqa: ARG001
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Caclulates the following metrics for the assets:
    - For the overall portfolio, on a daily basis:
        - Value of the portfolio.
        - Absoulte gain since start.
        - Percentage gain since start.
    - For each asset, on a daily basis:
        - Value of the asset.
        - Quantity of the asset.
    - Asset distribution (in value and percentage) as of latest date.

    Args:
        portfolio_data: Transactions history and other portfolio data.
        asset_prices: Daily prices of each asset as of Yahoo Finance.
        asset_dividends: Dataframe containing the dividend amount on the Ex-Dividend Date.
        sorting_columns: Columns to sort for each returned dataframe.

    Returns:
        Portfolio metrics, individual asset metrics and asset ditribution.
    """
    portfolio_model = pd.concat(
        [
            utils.calc_curr_qty(group, "asset")
            for _, group in (
                asset_prices.merge(
                    portfolio_data.transactions,
                    how="left",
                    on=["date", "ticker_asset"],
                )
                .assign(
                    trans_qty_asset=lambda df: df["trans_qty_asset"].fillna(0),
                    trans_val_asset=lambda df: df["trans_val_asset"].fillna(0),
                )
                .groupby("ticker_asset")
            )
        ],
    )

    dividends_company, dividends_year = _calc_dividends(
        asset_dividends.merge(
            portfolio_model[["date", "ticker_asset", "curr_qty_asset"]],
            how="left",
            on=["date", "ticker_asset"],
        ),
    )

    portfolio_model = utils.calc_curr_val(
        portfolio_model,
        "asset",
        sorting_columns=[{"columns": ["ticker_asset", "date"], "ascending": [True, False]}],
    )

    portfolio_val_evolution = _calc_val_evol(
        portfolio_model, sorting_columns=[{"columns": ["date"], "ascending": [False]}]
    )

    portfolio_gains = utils.calc_curr_gain(
        portfolio_val_evolution.merge(
            portfolio_data.transactions[["date", "trans_val_asset"]],
            how="left",
            on=["date"],
        )
        .assign(trans_val_asset=lambda df: df["trans_val_asset"].fillna(0))
        .rename(columns={"trans_val_asset": "trans_val_portfolio"}),
        "portfolio",
        sorting_columns=[{"columns": ["date"], "ascending": [False]}],
    )

    portfolio_yearly_gains = utils.calc_yearly_gain(portfolio_gains, "portfolio")

    asset_distribution = _calc_asset_dist(
        portfolio_model,
        portfolio_data,
        "asset",
    )

    return (
        portfolio_val_evolution.merge(  # type: ignore
            portfolio_gains.drop(columns=["money_out", "money_in"]),
            how="left",
            on=["date"],
        ),
        asset_distribution,
        portfolio_model,
        dividends_company,
        dividends_year,
        portfolio_yearly_gains,
    )


def _calc_asset_dist(
    portfolio_model: pd.DataFrame,
    portfolio_data: PortfolioData,
    position_type: str,
) -> pd.DataFrame:
    """Calculate the percentage in size each asset represents to the overall portfolio as well as
    the value of each asset, both at end date.

    Args:
        portfolio_model: Portfolio with curr_qty and curr_val for each asset.
        portfolio_data: Transactions history and other portfolio data.
        position_type: Type of position (asset, benchmark, etc).

    Returns:
        Dataframe with the percentage and value of each asset at end date.
    """
    asset_distribution = portfolio_model[portfolio_model["date"] == portfolio_data.end_date][
        [
            "date",
            f"ticker_{position_type}",
            f"curr_qty_{position_type}",
            f"curr_val_{position_type}",
        ]
    ].reset_index(
        drop=True,
    )

    return (
        asset_distribution[asset_distribution["curr_qty_asset"] != 0]
        .assign(
            percent=round(
                asset_distribution[f"curr_val_{position_type}"]
                / asset_distribution[f"curr_val_{position_type}"].sum()
                * 100,
                2,
            ),
            **{
                f"curr_val_{position_type}": round(
                    asset_distribution[f"curr_val_{position_type}"],
                    2,
                ),
            },
        )
        .sort_values([f"curr_val_{position_type}"], ascending=False)
        .reset_index(drop=True)
    )


def _calc_dividends(asset_dividends: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate the total dividend received for every asset.

    Args:
        asset_dividends: Dataframe containing the dividend amount on the Ex-Dividend Date.

    Raises:
        UnsortedError: Unsorted input data.

    Returns:
        Total dividends per company and total yearly dividends.
    """
    if not all(
        group[1].is_monotonic_decreasing
        for group in asset_dividends.groupby("ticker_asset")["date"]
    ):
        raise UnsortedError

    asset_dividends = asset_dividends.assign(
        total_dividend_asset=asset_dividends.groupby("ticker_asset")["curr_qty_asset"]
        .shift(
            -1,
        )  # shift one because we need to take into account yesterday's total shares hold on Ex-Dividend Date # noqa: E501
        .fillna(0)
        * asset_dividends["close_unadj_local_currency_dividends_asset"],
    )

    return (
        asset_dividends.groupby("ticker_asset")["total_dividend_asset"].sum().reset_index(),
        asset_dividends.groupby(asset_dividends["date"].dt.year)["total_dividend_asset"]
        .sum()
        .reset_index(),
    )


@sort_at_end()
def _calc_val_evol(
    portfolio_model: pd.DataFrame,
    sorting_columns: list[dict[str, list[str | bool]]],  # noqa: ARG001
) -> pd.DataFrame:
    """Calculate total daily value of the portfolio based on all the assets.

    Args:
        portfolio_model: Portfolio with curr_qty and curr_val for each asset.
        sorting_columns: Columns to sort for each returned dataframe.

    Raises:
        UnsortedError: Unsorted input data.

    Returns:
        Portfolio daily value.
    """
    if not all(
        group[1].is_monotonic_decreasing
        for group in portfolio_model.groupby("ticker_asset")["date"]
    ):
        raise UnsortedError

    return (
        portfolio_model.groupby(["date", "ticker_asset"])
        .first()
        .groupby("date")["curr_val_asset"]
        .sum()
        .reset_index()
        .assign(curr_val_portfolio=lambda df: round(df["curr_val_asset"], 2))
    )[["date", "curr_val_portfolio"]]
