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
    logger.info("Plotting portfolio absolute evolution.")
    _plot_portfolio_absolute_evolution(
        config,
        asset_portfolio_value_evolution,
        benchmark_value_evolution_absolute,
    )

    logger.info("Plotting portfolio percent evolution.")
    _plot_portfolio_percent_evolution(
        asset_portfolio_percent_evolution,
        benchmark_percent_evolution,
    )

    logger.info("Plotting asset distribution.")
    _plot_asset_distribution(config, asset_distribution)

    logger.info("Plotting individual assets vs benchmark.")
    _plot_individual_assets_vs_benchmark(individual_assets_vs_benchmark_returns)

    logger.info("End of generate reports.")


def _plot_portfolio_absolute_evolution(
    config: Config,
    asset_portfolio_value_evolution: pd.DataFrame,
    benchmark_value_evolution_absolute: pd.DataFrame,
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
        f"Date ({asset_portfolio_value_evolution['date'].iloc[-1].date().strftime('%d/%m/%Y')} - {asset_portfolio_value_evolution['date'].iloc[0].date().strftime('%d/%m/%Y')})",  # noqa: E501
    )
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(DIR_OUT / Path("portfolio_absolute_evolution.png"))
    plt.close()


def _plot_asset_distribution(
    config: Config,
    asset_distribution: pd.DataFrame,
) -> None:
    asset_distribution = asset_distribution.dropna()
    _, ax = plt.subplots(figsize=(10, 8))
    sizes = asset_distribution["current_value_asset"]
    tickers = asset_distribution["ticker_asset"]

    wedges, _, _ = ax.pie(
        sizes,
        labels=tickers,
        startangle=90,
        colors=plt.cm.Paired(range(len(tickers))),
        counterclock=False,
        autopct=lambda pct: f"{pct:.1f}%\n{(pct/100 * sum(asset_distribution['current_value_asset']) / 1000):.1f}k",  # noqa: E501
        wedgeprops={"width": 0.3},
    )

    legend_tickers = []
    for _, row in asset_distribution[
        ["ticker_asset", "current_value_asset", "percent", "current_quantity_asset"]
    ].iterrows():
        ticker, current_value_asset, percent, current_quantity = list(row)

        legend_tickers.append(
            f"{ticker}: {current_value_asset}{config.portfolio_currency.lower()} | {percent}% | {int(current_quantity)} shares",  # noqa: E501
        )

    ax.legend(wedges, legend_tickers, loc="center left", bbox_to_anchor=(-0.6, 0.5))
    ax.set(aspect="equal", title="Asset Distribution")

    plt.savefig(
        DIR_OUT / Path("asset_distribution.png"),
        bbox_inches="tight",
    )
    plt.close()


def _plot_portfolio_percent_evolution(
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
        f"Date ({benchmark_percent_evolution['date'].iloc[-1].date().strftime('%d/%m/%Y')} - {benchmark_percent_evolution['date'].iloc[0].date().strftime('%d/%m/%Y')})",  # noqa: E501
    )
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(
        DIR_OUT / Path("portfolio_percent_evolution.png"),
    )
    plt.close()


def _plot_individual_assets_vs_benchmark(
    individual_assets_vs_benchmark_returns: pd.DataFrame,
) -> None:
    plt.figure(figsize=(10, 6))

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

    ymin, _ = plt.ylim()
    y_offset = ymin - 5

    for i in index:
        plt.text(
            i,
            y_offset,
            f"{individual_assets_vs_benchmark_returns['current_percent_gain_asset'][i]:.2f}%",
            ha="center",
            color="blue",
            fontweight="bold",
            rotation=45,
        )
        plt.text(
            i + bar_width,
            y_offset,
            f"{individual_assets_vs_benchmark_returns['current_percent_gain_benchmark'][i]:.2f}%",
            ha="center",
            color="orange",
            fontweight="bold",
            rotation=45,
        )

    plt.ylabel("Percent gain (%)")
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
