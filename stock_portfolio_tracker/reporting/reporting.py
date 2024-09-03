"""Generate final reports."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger

from stock_portfolio_tracker.utils import Config

DIR_OUT = Path("/workspaces/Stock-Portfolio-Tracker/data/out/")


def generate_reports(
    config: Config,
    asset_portfolio_value_evolution: pd.DataFrame,
    asset_portfolio_percent_evolution: pd.DataFrame,
    asset_distribution: pd.DataFrame,
    benchmark_value_evolution_absolute: pd.DataFrame,
    individual_assets_vs_benchmark_returns: pd.DataFrame,
    benchmark_percent_evolution: pd.DataFrame,
) -> None:
    """Generate all final reports for the user.

    :param asset_portfolio_value_evolution: Stock portfolio hisorical price.
    :param benchmark_value_evolution_absolute: Benchmark hisorical price.
    """
    logger.info("Generating portfolio value evolution.")
    _generate_portfolio_value_evolution_plot(
        config,
        asset_portfolio_value_evolution,
        benchmark_value_evolution_absolute,
        "portfolio_value_evolution_absolute",
    )

    _generate_portfolio_percent_evolution_plot(
        asset_portfolio_percent_evolution,
        benchmark_percent_evolution,
    )

    logger.info("Generating portfolio current positions.")
    _plot_asset_distribution(config, asset_distribution)

    logger.info("Generating portfolio current positions.")
    _generate_individual_assets_vs_benchmark_returns(individual_assets_vs_benchmark_returns)

    logger.info("End of generate reports.")


def _generate_portfolio_value_evolution_plot(
    config: Config,
    asset_portfolio_value_evolution: pd.DataFrame,
    benchmark_value_evolution_absolute: pd.DataFrame,
    plot_name: str,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(
        asset_portfolio_value_evolution["date"],
        asset_portfolio_value_evolution["current_value_portfolio"],
        linestyle="-",
        color="blue",
        label=f"Portfolio value. Current: {asset_portfolio_value_evolution['current_value_portfolio'].iloc[0]} {config.portfolio_currency}",  # noqa: E501
    )
    plt.plot(
        benchmark_value_evolution_absolute["date"],
        benchmark_value_evolution_absolute["current_value_benchmark"],
        linestyle="-",
        color="orange",
        label=f"Benchmark value. Current: {benchmark_value_evolution_absolute['current_value_benchmark'].iloc[0]} {config.portfolio_currency}",  # noqa: E501
    )
    plt.xlabel("Date (YYYY-MM)")
    plt.ylabel(f"Value ({config.portfolio_currency})")
    plt.title(
        f"Date ({asset_portfolio_value_evolution['date'].iloc[-1].date()} - {asset_portfolio_value_evolution['date'].iloc[0].date()})",  # noqa: E501
    )
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(DIR_OUT / Path(f"{plot_name}.png"))
    plt.close()


def _plot_asset_distribution(
    config: Config,
    asset_distribution: pd.DataFrame,
) -> None:
    asset_distribution = asset_distribution.dropna()
    _, ax = plt.subplots(figsize=(10, 8))
    sizes = asset_distribution["current_position_value"]
    tickers = asset_distribution["ticker_asset"]

    wedges, _, _ = ax.pie(
        sizes,
        labels=tickers,
        startangle=90,
        colors=plt.cm.Paired(range(len(tickers))),
        counterclock=False,
        autopct=lambda pct: f"{pct:.1f}%\n{round(pct/100 * sum(asset_distribution['current_position_value']) / 1000, 1)}k",  # noqa: E501
        wedgeprops={"width": 0.3},
    )

    legend_tickers = []
    for _, row in asset_distribution[
        ["ticker_asset", "current_position_value", "percent", "current_quantity_asset"]
    ].iterrows():
        ticker, current_position_value, percent, current_quantity = list(row)

        legend_tickers.append(
            f"{ticker}: {current_position_value}{config.portfolio_currency.lower()} | {percent}% | {int(current_quantity)} shares",  # noqa: E501
        )

    ax.legend(wedges, legend_tickers, loc="center left", bbox_to_anchor=(-0.6, 0.5))
    ax.set(aspect="equal", title="Portfolio Distribution")

    plt.savefig(
        DIR_OUT / Path("asset_distribution.png"),
        bbox_inches="tight",
    )
    plt.close()


def _generate_portfolio_percent_evolution_plot(
    asset_portfolio_percent_evolution: pd.DataFrame,
    benchmark_percent_evolution: pd.DataFrame,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(
        asset_portfolio_percent_evolution["date"],
        asset_portfolio_percent_evolution["current_percent_gain_asset"],
        linestyle="-",
        color="blue",
        label=f"Portfolio. Current: {asset_portfolio_percent_evolution['current_percent_gain_asset'].iloc[0]} %",  # noqa: E501
    )
    plt.plot(
        benchmark_percent_evolution["date"],
        benchmark_percent_evolution["current_percent_gain_benchmark"],
        linestyle="-",
        color="orange",
        label=f"Benchmark. Current: {benchmark_percent_evolution['current_percent_gain_benchmark'].iloc[0]} %",  # noqa: E501
    )
    plt.xlabel("Date (YYYY-MM)")
    plt.ylabel("Percentage gain (%)")
    plt.title(
        f"Date ({benchmark_percent_evolution['date'].iloc[-1].date()} - {benchmark_percent_evolution['date'].iloc[0].date()})",  # noqa: E501
    )
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(
        DIR_OUT / Path("portfolio_percent_evolution.png"),
    )
    plt.close()


def _generate_individual_assets_vs_benchmark_returns(
    individual_assets_vs_benchmark_returns: pd.DataFrame,
) -> None:
    plt.figure(figsize=(10, 6))

    # plotting the bars
    bar_width = 0.4
    index = range(len(individual_assets_vs_benchmark_returns))

    plt.bar(
        index,
        individual_assets_vs_benchmark_returns["current_percent_gain_asset"],
        bar_width,
        label="Asset",
        color="blue",
    )
    plt.bar(
        [i + bar_width for i in index],
        individual_assets_vs_benchmark_returns["current_percent_gain_benchmark"],
        bar_width,
        label="Benchmark",
        color="orange",
    )

    # adding the values on top of the bars
    for i in index:
        plt.text(
            i,
            individual_assets_vs_benchmark_returns["current_percent_gain_asset"][i] + 1,
            f"{individual_assets_vs_benchmark_returns['current_percent_gain_asset'][i]:.2f}%",
            ha="center",
            color="blue",
            fontweight="bold",
        )
        plt.text(
            i + bar_width,
            individual_assets_vs_benchmark_returns["current_percent_gain_benchmark"][i] + 1,
            f"{individual_assets_vs_benchmark_returns['current_percent_gain_benchmark'][i]:.2f}%",
            ha="center",
            color="orange",
            fontweight="bold",
        )

    plt.xlabel("Ticker")
    plt.ylabel("Percent Gain (%)")
    plt.title("Current Percent Gain: Asset vs Benchmark")
    plt.xticks(
        [i + bar_width / 2 for i in index],
        individual_assets_vs_benchmark_returns["ticker_asset"],
    )
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        DIR_OUT
        / Path(
            "individual_assets_vs_benchmark_returns.png",
        ),
    )
    plt.close()
