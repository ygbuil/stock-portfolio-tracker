"""Generate final reports."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

from stock_portfolio_tracker.utils import Config

DIR_OUT = Path("/workspaces/Stock-Portfolio-Tracker/data/out/")


def generate_reports(
    config: Config,
    portfolio_evolution: pd.DataFrame,
    assets_distribution: pd.DataFrame,
    benchmark_val_evolution_abs: pd.DataFrame,
    assets_vs_benchmark: pd.DataFrame,
    benchmark_perc_evolution: pd.DataFrame,
) -> None:
    """Generate all final reports for the user.

    :param portfolio_evolution: Stock portfolio hisorical price.
    :param benchmark_val_evolution_abs: Benchmark hisorical price.
    """
    logger.info("Plotting portfolio absolute evolution.")
    _plot_portfolio_absolute_evolution(
        config,
        portfolio_evolution,
        benchmark_val_evolution_abs,
    )

    logger.info("Plotting portfolio percent evolution.")
    _plot_portfolio_percent_evolution(
        portfolio_evolution,
        benchmark_perc_evolution,
    )

    logger.info("Plotting asset distribution.")
    _plot_assets_distribution(config, assets_distribution)

    logger.info("Plotting individual assets vs benchmark.")
    _plot_assets_vs_benchmark(assets_vs_benchmark)

    logger.info("End of generate reports.")


def _plot_portfolio_absolute_evolution(
    config: Config,
    portfolio_evolution: pd.DataFrame,
    benchmark_val_evolution_abs: pd.DataFrame,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(
        portfolio_evolution["date"],
        portfolio_evolution["curr_val_portfolio"],
        linestyle="-",
        color="blue",
        label=f"Portfolio value. Current: {portfolio_evolution['curr_val_portfolio'].iloc[0]} {config.portfolio_currency}",  # noqa: E501
    )
    plt.plot(
        benchmark_val_evolution_abs["date"],
        benchmark_val_evolution_abs["curr_val_benchmark"],
        linestyle="-",
        color="orange",
        label=f"Benchmark value. Current: {benchmark_val_evolution_abs['curr_val_benchmark'].iloc[0]} {config.portfolio_currency}",  # noqa: E501
    )
    plt.xlabel("Date (YYYY-MM)")
    plt.ylabel(f"Value ({config.portfolio_currency})")
    plt.title(
        f"Date ({portfolio_evolution['date'].iloc[-1].date().strftime('%d/%m/%Y')} - {portfolio_evolution['date'].iloc[0].date().strftime('%d/%m/%Y')})",  # noqa: E501
    )
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(DIR_OUT / Path("portfolio_absolute_evolution.png"))
    plt.close()


def _plot_assets_distribution(
    config: Config,
    assets_distribution: pd.DataFrame,
) -> None:
    assets_distribution = assets_distribution.dropna()
    _, ax = plt.subplots(figsize=(10, 8))
    sizes = assets_distribution["curr_val_asset"]
    tickers = assets_distribution["ticker_asset"]

    wedges, _, _ = ax.pie(  # type: ignore[reportAssignmentType]
        sizes,
        labels=tickers,  # type: ignore[reportArgumentType]
        startangle=90,
        colors=plt.cm.Paired(range(len(tickers))),  # type: ignore[reportArgumentType]
        counterclock=False,
        autopct=lambda pct: f"{pct:.1f}%\n{(pct/100 * sum(assets_distribution['curr_val_asset']) / 1000):.1f}k",  # noqa: E501
        wedgeprops={"width": 0.3},
    )

    legend_tickers = []
    for _, row in assets_distribution[
        ["ticker_asset", "curr_val_asset", "percent", "curr_qty_asset"]
    ].iterrows():
        ticker, curr_val_asset, percent, curr_qty = list(row)

        legend_tickers.append(
            f"{ticker}: {curr_val_asset}{config.portfolio_currency.lower()} | {percent}% | {int(curr_qty)} shares",  # noqa: E501
        )

    ax.legend(wedges, legend_tickers, loc="center left", bbox_to_anchor=(-0.6, 0.5))
    ax.set(aspect="equal", title="Asset Distribution")

    plt.savefig(
        DIR_OUT / Path("assets_distribution.png"),
        bbox_inches="tight",
    )
    plt.close()


def _plot_portfolio_percent_evolution(
    portfolio_evolution: pd.DataFrame,
    benchmark_perc_evolution: pd.DataFrame,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(
        portfolio_evolution["date"],
        portfolio_evolution["curr_perc_gain_portfolio"],
        linestyle="-",
        color="blue",
        label=f"Portfolio. Current: {portfolio_evolution['curr_perc_gain_portfolio'].iloc[0]} %",
    )
    plt.plot(
        benchmark_perc_evolution["date"],
        benchmark_perc_evolution["curr_perc_gain_benchmark"],
        linestyle="-",
        color="orange",
        label=f"Benchmark. Current: {benchmark_perc_evolution['curr_perc_gain_benchmark'].iloc[0]} %",  # noqa: E501
    )
    plt.xlabel("Date (YYYY-MM)")
    plt.ylabel("Percentage gain (%)")
    plt.title(
        f"Date ({benchmark_perc_evolution['date'].iloc[-1].date().strftime('%d/%m/%Y')} - {benchmark_perc_evolution['date'].iloc[0].date().strftime('%d/%m/%Y')})",  # noqa: E501
    )
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(
        DIR_OUT / Path("portfolio_percent_evolution.png"),
    )
    plt.close()


def _plot_assets_vs_benchmark(
    assets_vs_benchmark: pd.DataFrame,
) -> None:
    tickers, asset_gains, benchmark_gains = (
        assets_vs_benchmark["ticker_asset"],
        assets_vs_benchmark["curr_perc_gain_asset"],
        assets_vs_benchmark["curr_perc_gain_benchmark"],
    )
    n = len(tickers)
    bar_width = 0.4
    index = np.arange(n)

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.bar(index, asset_gains, bar_width, label="Asset Gains", color="blue")
    ax.bar(index + bar_width, benchmark_gains, bar_width, label="Benchmark Gains", color="orange")

    top_y_lim = max(list(asset_gains) + list(benchmark_gains))
    bottom_y_lim = min(list(asset_gains) + list(benchmark_gains))
    margin = (abs(top_y_lim) + abs(bottom_y_lim)) * 0.02

    top_y_lim += margin
    bottom_y_lim -= margin
    y_len = abs(top_y_lim) + abs(bottom_y_lim)

    # Set fixed axis limits (frame position)
    ax.set_xlim((-0.5, n))
    ax.set_ylim((bottom_y_lim, top_y_lim))

    # Add labels and title
    ax.set_ylabel("Percentage Gain (%)")
    ax.set_title("Asset vs Benchmark Percentage Gains")
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(tickers)

    # Add legend
    ax.legend()

    y_offset = bottom_y_lim - y_len * 0.12

    for i in index:
        plt.text(
            i,
            y_offset,
            f"{assets_vs_benchmark['curr_perc_gain_asset'][i]:.2f}%",
            ha="center",
            color="blue",
            fontweight="bold",
            rotation=40,
        )
        plt.text(
            i + bar_width,
            y_offset,
            f"{assets_vs_benchmark['curr_perc_gain_benchmark'][i]:.2f}%",
            ha="center",
            color="orange",
            fontweight="bold",
            rotation=40,
        )

    plt.savefig(
        DIR_OUT
        / Path(
            "assets_vs_benchmark.png",
        ),
    )
    plt.close()
