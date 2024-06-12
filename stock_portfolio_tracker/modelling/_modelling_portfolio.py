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

    asset_portfolio_percent_evolution = pd.merge(
        asset_portfolio_value_evolution,
        portfolio_data.transactions,
        "left",
        on=["date"],
    )
    asset_portfolio_percent_evolution = calculate_current_percent_gain(
        asset_portfolio_percent_evolution,
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


def calculate_current_percent_gain(df: pd.DataFrame) -> pd.DataFrame:
    df = utils.sort_by_columns(
        df,
        ["date"],
        [True],
    )

    for date in df["date"]:
        df.loc[df["date"] == date, "money_out"] = sum(
            df[(df["date"] < date) & (df["value"] < 0)]["value"],
        )
        if len(df[df["date"] == date - pd.Timedelta(days=1)]["portfolio_value"]) > 0:
            latest_portfolio_value = df[df["date"] == date - pd.Timedelta(days=1)][
                "portfolio_value"
            ].iloc[0]
        else:
            latest_portfolio_value = 0
        df.loc[df["date"] == date, "money_in"] = (
            sum(df[(df["date"] < date) & (df["value"] > 0)]["value"]) + latest_portfolio_value
        )

    return (
        df.assign(
            current_gain=lambda df: df["money_out"] + df["money_in"],
            current_percent_gain=lambda df: df.apply(
                lambda x: round((abs(x["money_in"] / x["money_out"]) - 1) * 100, 2)
                if x["money_out"] != 0
                else 0,
                axis=1,
            ),
        )
        .groupby("date")
        .last()
        .reset_index()
    )[["date", "current_gain", "current_percent_gain"]]
