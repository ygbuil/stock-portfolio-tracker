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
    benchmark_evolution: pd.DataFrame,
    asset_distribution: pd.DataFrame,
    assets_vs_benchmark: pd.DataFrame,
    dividends_company: pd.DataFrame,
    dividends_year: pd.DataFrame,
) -> None:
    """Generate all final reports for the user.

    Args:
        config: Config class.
        portfolio_evolution: Portfolio value and gains evolution.
        benchmark_evolution: Benchmark value and gains evolution.
        asset_distribution: Percentage and amount of each asset held.
        assets_vs_benchmark: Individual asset percetnage returns vs benchmark.
        dividends_company: Total dividends paied by company.
        dividends_year: Total dividends paied by year.
    """
    logger.info("Plotting portfolio value evolution.")
    _plot_portfolio_value_evolution(
        config,
        portfolio_evolution,
        benchmark_evolution,
    )

    logger.info("Plotting portfolio gain evolution.")
    _plot_portfolio_gain_evolution(
        config.portfolio_currency,
        portfolio_evolution,
        benchmark_evolution,
        "abs",
    )

    _plot_portfolio_gain_evolution(
        config.portfolio_currency,
        portfolio_evolution,
        benchmark_evolution,
        "perc",
    )

    logger.info("Plotting asset distribution.")
    _plot_asset_distribution(config, asset_distribution)

    logger.info("Plotting individual assets vs benchmark.")
    _plot_assets_vs_benchmark(assets_vs_benchmark)

    logger.info("Plotting dividends by company.")
    _plot_dividends_company(config.portfolio_currency, dividends_company)

    logger.info("Plotting dividends by year.")
    _plot_dividends_year(config.portfolio_currency, dividends_year)

    logger.info("End of generate reports.")


def _plot_portfolio_value_evolution(
    config: Config,
    portfolio_evolution: pd.DataFrame,
    benchmark_evolution: pd.DataFrame,
) -> None:
    """Plot portfolio value evolution.

    Args:
        config: Config class.
        portfolio_evolution: Portfolio value and gains evolution.
        benchmark_evolution: Benchmark value and gains evolution.
    """
    plt.figure(figsize=(10, 6))
    plt.plot(
        portfolio_evolution["date"],
        portfolio_evolution["curr_val_portfolio"],
        linestyle="-",
        color="blue",
        label=f"Portfolio value. Current: {portfolio_evolution['curr_val_portfolio'].iloc[0]} {config.portfolio_currency}",  # noqa: E501
    )
    plt.plot(
        benchmark_evolution["date"],
        benchmark_evolution["curr_val_benchmark"],
        linestyle="-",
        color="orange",
        label=f"Benchmark value. Current: {benchmark_evolution['curr_val_benchmark'].iloc[0]} {config.portfolio_currency}",  # noqa: E501
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
    plt.savefig(DIR_OUT / Path("portfolio_value_evolution.png"))
    plt.close()


def _plot_asset_distribution(
    config: Config,
    asset_distribution: pd.DataFrame,
) -> None:
    """Plot asset distribution.

    Args:
        config: Config class.
        asset_distribution: Percentage and amount of each asset held.
    """
    asset_distribution = asset_distribution.dropna()
    _, ax = plt.subplots(figsize=(10, 8))
    sizes = asset_distribution["curr_val_asset"]
    tickers = asset_distribution["ticker_asset"]

    wedges, _, _ = ax.pie(  # type: ignore
        sizes,
        labels=tickers,  # type: ignore
        startangle=90,
        colors=plt.cm.Paired(range(len(tickers))),  # type: ignore
        counterclock=False,
        autopct=lambda pct: f"{pct:.1f}%\n{(pct/100 * sum(asset_distribution['curr_val_asset']) / 1000):.1f}k",  # noqa: E501
        wedgeprops={"width": 0.3},
    )

    legend_tickers = []
    for _, row in asset_distribution[
        ["ticker_asset", "curr_val_asset", "percent", "curr_qty_asset"]
    ].iterrows():
        ticker, curr_val_asset, percent, curr_qty = list(row)

        legend_tickers.append(
            f"{ticker}: {curr_val_asset}{config.portfolio_currency.lower()} | {percent}% | {int(curr_qty)} shares",  # noqa: E501
        )

    ax.legend(wedges, legend_tickers, loc="center left", bbox_to_anchor=(-0.6, 0.5))
    ax.set(aspect="equal", title="Asset Distribution")

    plt.savefig(
        DIR_OUT / Path("asset_distribution.png"),
        bbox_inches="tight",
    )
    plt.close()


def _plot_portfolio_gain_evolution(
    portfolio_currency: str,
    portfolio_evolution: pd.DataFrame,
    benchmark_evolution: pd.DataFrame,
    gain_type: str,
) -> None:
    """Plot portfolio gain evolution.

    Args:
        portfolio_currency: Currency of the portfolio.
        portfolio_evolution: Portfolio value and gains evolution.
        benchmark_evolution: Benchmark value and gains evolution.
        gain_type: Type of gain. "perc" or "abs".
    """
    unit = "%" if gain_type == "perc" else portfolio_currency
    plt.figure(figsize=(10, 6))
    plt.plot(
        portfolio_evolution["date"],
        portfolio_evolution[f"curr_{gain_type}_gain_portfolio"],
        linestyle="-",
        color="blue",
        label=f"Portfolio. Current: {portfolio_evolution[f'curr_{gain_type}_gain_portfolio'].iloc[0]} {unit}",  # noqa: E501
    )
    plt.plot(
        benchmark_evolution["date"],
        benchmark_evolution[f"curr_{gain_type}_gain_benchmark"],
        linestyle="-",
        color="orange",
        label=f"Benchmark. Current: {benchmark_evolution[f'curr_{gain_type}_gain_benchmark'].iloc[0]} {unit}",  # noqa: E501
    )
    plt.xlabel("Date (YYYY-MM)")
    plt.ylabel(f"{gain_type[0].upper() + gain_type[1:]} gain ({unit})")
    plt.title(
        f"Date ({benchmark_evolution['date'].iloc[-1].date().strftime('%d/%m/%Y')} - {benchmark_evolution['date'].iloc[0].date().strftime('%d/%m/%Y')})",  # noqa: E501
    )
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(
        DIR_OUT / Path(f"portfolio_{gain_type}_gain_evolution.png"),
    )
    plt.close()


def _plot_assets_vs_benchmark(
    assets_vs_benchmark: pd.DataFrame,
) -> None:
    """Plot assets vs benchmark.

    Args:
        assets_vs_benchmark: Individual asset percetnage returns vs benchmark.
    """
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


def _plot_dividends_company(
    portfolio_currency: str,
    dividends_company: pd.DataFrame,
) -> None:
    """Plot dividends company.

    Args:
        portfolio_currency: Currency of the portfolio.
        dividends_company: Total dividends paied by company.
    """
    tickers, dividends = (
        dividends_company["ticker_asset"],
        dividends_company["total_dividend_asset"],
    )
    n = len(tickers)
    bar_width = 0.4
    index = np.arange(n)

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.bar(index, dividends, bar_width, label="Dividend amount", color="blue")

    top_y_lim = max(list(dividends))
    bottom_y_lim = min(list(dividends))
    margin = (abs(top_y_lim) + abs(bottom_y_lim)) * 0.02

    top_y_lim += margin
    bottom_y_lim -= margin
    y_len = abs(top_y_lim) + abs(bottom_y_lim)

    # Set fixed axis limits (frame position)
    ax.set_xlim((-0.5, n))
    ax.set_ylim((bottom_y_lim, top_y_lim))

    # Add labels and title
    ax.set_ylabel("Dividend amount (EUR)")
    ax.set_title("Dividends per company")
    ax.set_xticks(index)
    ax.set_xticklabels(tickers)

    # Add legend
    ax.legend()

    y_offset = bottom_y_lim - y_len * 0.11

    for i in index:
        plt.text(
            i,
            y_offset,
            f"{dividends_company['total_dividend_asset'][i]:.2f}\n{portfolio_currency}",
            ha="center",
            color="blue",
            fontweight="bold",
            rotation=0,
        )

    plt.savefig(
        DIR_OUT
        / Path(
            "dividends_company.png",
        ),
    )
    plt.close()


def _plot_dividends_year(portfolio_currency: str, dividends_year: pd.DataFrame) -> None:
    """Plot dividends year.

    Args:
        portfolio_currency: Currency of the portfolio.
        dividends_year: Total dividends paied by year.
    """
    years, dividends = (
        dividends_year["date"],
        dividends_year["total_dividend_asset"],
    )
    n = len(dividends)
    bar_width = 0.4
    index = np.arange(n)

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.bar(index, dividends, bar_width, label="Dividend amount", color="blue")

    top_y_lim = max(list(dividends))
    bottom_y_lim = min(list(dividends))
    margin = (abs(top_y_lim) + abs(bottom_y_lim)) * 0.02

    top_y_lim += margin
    bottom_y_lim -= margin
    y_len = abs(top_y_lim) + abs(bottom_y_lim)

    # Set fixed axis limits (frame position)
    ax.set_xlim((-0.5, n))
    ax.set_ylim((bottom_y_lim, top_y_lim))

    # Add labels and title
    ax.set_ylabel("Dividend amount (EUR)")
    ax.set_title("Dividends per year")
    ax.set_xticks(index)
    ax.set_xticklabels(years)

    # Add legend
    ax.legend()

    y_offset = bottom_y_lim - y_len * 0.11

    for i in index:
        plt.text(
            i,
            y_offset,
            f"{dividends_year['total_dividend_asset'][i]:.2f}\n{portfolio_currency}",
            ha="center",
            color="blue",
            fontweight="bold",
            rotation=0,
        )

    plt.savefig(
        DIR_OUT
        / Path(
            "dividends_year.png",
        ),
    )
    plt.close()
