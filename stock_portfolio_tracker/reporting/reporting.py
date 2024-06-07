"""Generate final reports."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from loguru import logger


def generate_reports(
    stock_portfolio_value_evolution: pd.DataFrame,
    benchmark_value_evolution: pd.DataFrame,
) -> None:
    """Generate all final reports for the user.

    :param stock_portfolio_value_evolution: Stock portfolio hisorical price.
    :param benchmark_value_evolution: Benchmark hisorical price.
    """
    logger.info("Start of generate reports.")

    _save_plots(stock_portfolio_value_evolution, benchmark_value_evolution)

    logger.info("End of generate reports.")


def _save_plots(
    stock_portfolio_value_evolution: pd.DataFrame,
    benchmark_value_evolution: pd.DataFrame,
) -> None:
    plot_filename = Path("/workspaces/Stock-Portfolio-Tracker/data/out/plot.png")

    plt.figure(figsize=(10, 6))
    plt.plot(
        stock_portfolio_value_evolution["date"],
        stock_portfolio_value_evolution["portfolio_value"],
        linestyle="-",
        color="blue",
        label="Portfolio value",
    )
    plt.plot(
        benchmark_value_evolution["date"],
        benchmark_value_evolution["benchmark_value"],
        linestyle="-",
        color="orange",
        label="Benchmark value",
    )
    plt.xlabel("Date")
    plt.ylabel("Value")
    plt.title("Value Over Time")
    plt.grid(True)  # noqa: FBT003
    plt.xticks(rotation=45)
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(plot_filename)
    plt.close()
