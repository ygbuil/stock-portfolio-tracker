"""Generate final reports."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from loguru import logger

from stock_portfolio_tracker import utils
from stock_portfolio_tracker.utils import Config, PositionStatus

DIR_OUT = Path("/workspaces/Stock-Portfolio-Tracker/data/out/")


def generate_reports(
    config: Config,
    portfolio_evolution: pd.DataFrame,
    benchmark_evolution: pd.DataFrame,
    asset_distribution: pd.DataFrame,
    assets_vs_benchmark: pd.DataFrame,
    dividends_company: pd.DataFrame,
    dividends_year: pd.DataFrame,
    yearly_returns: pd.DataFrame,
    overall_returns: pd.DataFrame,
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
        yearly_returns: Yearly gains.
        overall_returns: Return metrics for the entire portfolio lifetime.
    """
    logger.info("Cleaning current output artifacts.")
    utils.delete_current_artifacts(DIR_OUT)

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
    _plot_portfolio_gain_evolution_diff(portfolio_evolution, benchmark_evolution)

    logger.info("Plotting asset distribution.")
    _plot_asset_distribution(config, asset_distribution)

    logger.info("Plotting individual assets vs benchmark.")
    for position_status in [PositionStatus.OPEN.value, PositionStatus.CLOSED.value]:
        _plot_barchar_2_cols(
            df=assets_vs_benchmark[assets_vs_benchmark["position_status"] == position_status],
            col_name_x_labels="ticker_asset",
            col_name_bars_1="curr_perc_gain_asset",
            col_name_bars_2="curr_perc_gain_benchmark",
            y_axis_title="Percentage Gain (%)",
            plot_title="Assets vs benchmark",
            plot_folder="assets_vs_benchmark",
            plot_name=f"assets_vs_benchmark_{position_status}",
        )

    logger.info("Plotting dividends by company.")
    _plot_dividends_company(config.portfolio_currency, dividends_company)

    logger.info("Plotting dividends by year.")
    _plot_dividends_year(config.portfolio_currency, dividends_year)

    logger.info("Plotting yearly gains.")
    _plot_overall_returns(overall_returns)
    for return_type in ["simple_return", "twr"]:
        _plot_barchar_2_cols(
            df=yearly_returns.sort_values(by="year"),
            col_name_x_labels="year",
            col_name_bars_1=f"{return_type}_portfolio",
            col_name_bars_2=f"{return_type}_benchmark",
            y_axis_title=utils.parse_underscore_text(return_type),
            plot_title=utils.parse_underscore_text(return_type),
            plot_folder="summary_returns",
            plot_name=return_type,
        )
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
    output_path = DIR_OUT / "portfolio_evolution" / "total_value.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
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
        autopct=lambda pct: f"{pct:.1f}%\n{(pct / 100 * sum(asset_distribution['curr_val_asset']) / 1000):.1f}k",  # noqa: E501
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

    output_path = DIR_OUT / "asset_distribution" / "asset_distribution.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
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
    output_path = DIR_OUT / "portfolio_evolution" / f"{gain_type}_gain.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def _plot_portfolio_gain_evolution_diff(
    portfolio_evolution: pd.DataFrame,
    benchmark_evolution: pd.DataFrame,
) -> None:
    """Plot portfolio gain evolution.

    Args:
        portfolio_currency: Currency of the portfolio.
        portfolio_evolution: Portfolio value and gains evolution.
        benchmark_evolution: Benchmark value and gains evolution.
        gain_type: Type of gain. "perc" or "abs".
    """
    plt.figure(figsize=(10, 6))
    plt.plot(
        portfolio_evolution["date"],
        portfolio_evolution["curr_perc_gain_portfolio"]
        - benchmark_evolution["curr_perc_gain_benchmark"],
        linestyle="-",
        color="blue",
        label=f"Current outperformance: {round(portfolio_evolution['curr_perc_gain_portfolio'].iloc[0] - benchmark_evolution['curr_perc_gain_benchmark'].iloc[0], 2)} percentage points",  # noqa: E501
    )
    plt.xlabel("Date (YYYY-MM)")
    plt.ylabel("Perc gain diff (percentage points)")
    plt.title(
        f"Date ({benchmark_evolution['date'].iloc[-1].date().strftime('%d/%m/%Y')} - {benchmark_evolution['date'].iloc[0].date().strftime('%d/%m/%Y')})",  # noqa: E501
    )
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.axhline(y=0, color="red", linestyle="--")
    plt.legend(loc="best")
    plt.tight_layout()
    output_path = DIR_OUT / "portfolio_evolution" / "perc_gain_diff.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()


def _plot_barchar_2_cols(
    df: pd.DataFrame,
    col_name_x_labels: str,
    col_name_bars_1: str,
    col_name_bars_2: str,
    y_axis_title: str,
    plot_title: str,
    plot_folder: str,
    plot_name: str,
) -> None:
    """Plot a bar chart comparing two columns of data.

    Args:
        df: DataFrame containing the data to be plotted.
        col_name_x_labels: Column name for the x-axis labels.
        col_name_bars_1: Column name for the first set of bars.
        col_name_bars_2: Column name for the second set of bars.
        y_axis_title: Label for the y-axis.
        plot_title: Title of the plot.
        plot_folder: Directory where the plot will be saved.
        plot_name: Name of the output plot file.
    """
    x_labels, bars_1, bars_2 = (
        df[col_name_x_labels],
        df[col_name_bars_1],
        df[col_name_bars_2],
    )
    n = len(x_labels)
    bar_width = 0.4
    index = np.arange(n)

    fig, ax = plt.subplots(figsize=(12, 7))

    ax.bar(index, bars_1, bar_width, label=col_name_bars_1, color="blue")
    ax.bar(index + bar_width, bars_2, bar_width, label=col_name_bars_2, color="orange")

    top_y_lim = max(list(bars_1) + list(bars_2))
    bottom_y_lim = min(list(bars_1) + list(bars_2))
    margin = (abs(top_y_lim) + abs(bottom_y_lim)) * 0.02

    top_y_lim += margin
    bottom_y_lim -= margin
    y_len = abs(top_y_lim) + abs(bottom_y_lim)

    # Set fixed axis limits (frame position)
    ax.set_xlim((-0.5, n))
    ax.set_ylim((bottom_y_lim, top_y_lim))

    # Add labels and title
    ax.set_ylabel(y_axis_title)
    ax.set_title(plot_title)
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(x_labels)

    # Add legend
    ax.legend()

    y_offset = bottom_y_lim - y_len * 0.12

    for i in index:
        plt.text(
            i,  # type: ignore
            y_offset,
            f"{bars_1.iloc[i]:.2f}%",
            ha="center",
            color="blue",
            fontweight="bold",
            rotation=40,
        )
        plt.text(
            i + bar_width,
            y_offset,
            f"{bars_2.iloc[i]:.2f}%",
            ha="center",
            color="orange",
            fontweight="bold",
            rotation=40,
        )

    output_path = DIR_OUT / plot_folder / f"{plot_name}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
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
            i,  # type: ignore
            y_offset,
            f"{dividends_company['total_dividend_asset'][i]:.2f}\n{portfolio_currency}",  # type: ignore
            ha="center",
            color="blue",
            fontweight="bold",
            rotation=0,
        )

    output_path = DIR_OUT / "dividends" / "dividends_by_company.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
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
            i,  # type: ignore
            y_offset,
            f"{dividends_year['total_dividend_asset'][i]:.2f}\n{portfolio_currency}",  # type: ignore
            ha="center",
            color="blue",
            fontweight="bold",
            rotation=0,
        )

    output_path = DIR_OUT / "dividends" / "dividends_by_year.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path)
    plt.close()


def _plot_overall_returns(overall_returns: pd.DataFrame) -> None:
    """Plot overall gains.

    Args:
        overall_returns: Overall returns.
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.set_axis_off()  # Hide axes

    ax.table(
        cellText=overall_returns.values,  # type: ignore
        colLabels=overall_returns.columns,  # type: ignore
        cellLoc="center",
        loc="center",
    )

    plt.tight_layout()
    output_path = DIR_OUT / "summary_returns" / "summary_returns.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()
