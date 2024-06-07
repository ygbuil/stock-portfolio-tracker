"""Generate final reports."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def generate_report(
    stock_portfolio_value_evolution: pd.DataFrame,
    benchmark_value_evolution: pd.DataFrame,
) -> None:
    """Generate all final reports for the user."""
    _save_plots(stock_portfolio_value_evolution, benchmark_value_evolution)


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
