"""Generate final reports."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger
from objetcs import Config


def generate_reports(
    config: Config,
    asset_portfolio_value_evolution: pd.DataFrame,
    asset_portfolio_percent_evolution: pd.DataFrame,
    asset_portfolio_current_positions: pd.DataFrame,
    benchmark_value_evolution: pd.DataFrame,
) -> None:
    """Generate all final reports for the user.

    :param asset_portfolio_value_evolution: Stock portfolio hisorical price.
    :param benchmark_value_evolution: Benchmark hisorical price.
    """
    logger.info("Start of generate reports.")

    logger.info("Generating portfolio value evolution.")
    _generate_portfolio_value_evolution_plot(
        config,
        asset_portfolio_value_evolution,
        benchmark_value_evolution,
    )

    _generate_portfolio_percent_evolution_plot(
        asset_portfolio_percent_evolution,
    )

    logger.info("Generating portfolio current positions.")
    _generate_portfolio_current_positions_plot(config, asset_portfolio_current_positions)

    logger.info("End of generate reports.")


def _generate_portfolio_value_evolution_plot(
    config: Config,
    asset_portfolio_value_evolution: pd.DataFrame,
    benchmark_value_evolution: pd.DataFrame,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(
        asset_portfolio_value_evolution["date"],
        asset_portfolio_value_evolution["portfolio_value"],
        linestyle="-",
        color="blue",
        label=f"Portfolio value. Current: {asset_portfolio_value_evolution['portfolio_value'].iloc[0]} {config.portfolio_currency}",  # noqa: E501
    )
    plt.plot(
        benchmark_value_evolution["date"],
        benchmark_value_evolution["benchmark_value"],
        linestyle="-",
        color="orange",
        label=f"Benchmark value. Current: {benchmark_value_evolution['benchmark_value'].iloc[0]} {config.portfolio_currency}",  # noqa: E501
    )
    plt.xlabel("Date (YYYY-MM)")
    plt.ylabel(f"Value ({config.portfolio_currency})")
    plt.title("Value Over Time")
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(Path("/workspaces/Stock-Portfolio-Tracker/data/out/portfolio_value_evolution.png"))
    plt.close()


def _generate_portfolio_current_positions_plot(
    config: Config,
    asset_portfolio_current_positions: pd.DataFrame,
) -> None:
    asset_portfolio_current_positions = asset_portfolio_current_positions.dropna()
    _, ax = plt.subplots(figsize=(10, 8))
    sizes = asset_portfolio_current_positions["current_position_value"]
    tickers = asset_portfolio_current_positions["asset_ticker"]

    wedges, _, _ = ax.pie(
        sizes,
        labels=tickers,
        startangle=90,
        colors=plt.cm.Paired(range(len(tickers))),
        counterclock=False,
        autopct=lambda pct: f"{pct:.1f}%\n{round(pct/100 * sum(asset_portfolio_current_positions['current_position_value']) / 1000, 1)}k",  # noqa: E501
        wedgeprops={"width": 0.3},
    )

    legend_tickers = []
    for _, row in asset_portfolio_current_positions[
        ["asset_ticker", "current_position_value", "percent", "current_quantity"]
    ].iterrows():
        ticker, current_position_value, percent, current_quantity = list(row)

        legend_tickers.append(
            f"{ticker}: {current_position_value}{config.portfolio_currency.lower()} | {percent}% | {int(current_quantity)} shares",  # noqa: E501
        )

    ax.legend(wedges, legend_tickers, loc="center left", bbox_to_anchor=(-0.6, 0.5))
    ax.set(aspect="equal", title="Portfolio Distribution")

    plt.savefig(
        Path("/workspaces/Stock-Portfolio-Tracker/data/out/portfolio_current_positions.png"),
        bbox_inches="tight",
    )
    plt.close()


def _generate_portfolio_percent_evolution_plot(
    asset_portfolio_percent_evolution: pd.DataFrame,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(
        asset_portfolio_percent_evolution["date"],
        asset_portfolio_percent_evolution["current_percent_gain"],
        linestyle="-",
        color="blue",
        label=f"Percentage gain. Current: {asset_portfolio_percent_evolution['current_percent_gain'].iloc[0]} %",  # noqa: E501
    )
    plt.xlabel("Date (YYYY-MM)")
    plt.ylabel("Percentage gain (%)")
    plt.title("Value Over Time")
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(
        Path("/workspaces/Stock-Portfolio-Tracker/data/out/portfolio_percent_evolution.png"),
    )
    plt.close()
