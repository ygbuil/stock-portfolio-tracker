import numpy as np
import pandas as pd

from stock_portfolio_tracker.exceptions import UnsortedError
from stock_portfolio_tracker.utils import PortfolioData, PositionStatus, PositionType, sort_at_end

from . import _utils as utils


@sort_at_end()
def model_benchmark(
    portfolio_data: PortfolioData,
    benchmark_prices: pd.DataFrame,
    sorting_columns: list[dict[str, list[str | bool]]],  # noqa: ARG001
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Model the benchmark as if the same transaction value purchased of an asset of the portfolio
    was purchased of the benchmark (in absoulte value). Under these simulation assumptions, the
    metrics calculated are, on a daily basis:
        - Value of the benchmark held.
        - Percentage gain since the start.

    Args:
        portfolio_data: Transactions history and other portfolio data.
        benchmark_prices: Benchmark historical data.
        sorting_columns: Columns to sort for each returned dataframe.

    Returns:
        DataFrames with benchmark value and percentage gain.
    """
    benchmark_val_evolution_abs = _simulate_benchmark_absolute(benchmark_prices, portfolio_data)

    benchmark_val_evolution_abs = utils.calc_curr_qty(
        benchmark_val_evolution_abs,
        PositionType.BENCHMARK,
    )

    benchmark_val_evolution_abs = utils.calc_curr_val(
        benchmark_val_evolution_abs,
        PositionType.BENCHMARK,
        sorting_columns=[{"columns": ["ticker_benchmark", "date"], "ascending": [True, False]}],
    )

    benchmark_val_evolution_abs = (
        benchmark_val_evolution_abs.groupby("date")
        .first()  # get the latest current state when there are multiple transactions at the same day for a ticker # noqa: E501
        .reset_index()
        .sort_values(by=["date"], ascending=[False])
        .reset_index(drop=True)
        .assign(curr_val_benchmark=lambda df: round(df["curr_val_benchmark"], 2))
    )

    benchmark_gains = utils.calc_simple_return_daily(
        benchmark_val_evolution_abs[["date", "ticker_benchmark", "curr_val_benchmark"]]
        .merge(
            portfolio_data.transactions[["date", "trans_val_asset"]],
            how="left",
            on=["date"],
        )
        .assign(trans_val_asset=lambda df: df["trans_val_asset"].fillna(0))
        .rename(columns={"trans_val_asset": "trans_val_benchmark"}),
        PositionType.BENCHMARK,
        sorting_columns=[{"columns": ["date"], "ascending": [False]}],
    )

    benchmark_returns = utils.calc_overall_returns(benchmark_gains, PositionType.BENCHMARK)

    return (
        benchmark_val_evolution_abs[["date", "curr_val_benchmark"]].merge(
            benchmark_gains.drop(
                columns=["curr_val_benchmark", "trans_val_benchmark", "money_out", "money_in"]
            ),
            how="left",
            on=["date"],
        ),
        benchmark_returns,
    )


@sort_at_end()
def model_assets_vs_benchmark(
    portfolio_model: pd.DataFrame,
    benchmark_prices: pd.DataFrame,
    sorting_columns: list[dict[str, list[str | bool]]],  # noqa: ARG001
) -> pd.DataFrame:
    """Compare individual asset performance against the benchmark proportionally, as explained in
    _simulate_benchmark_proportional().

    Args:
        portfolio_model: Portfolio with curr_qty and curr_val for each asset.
        benchmark_prices: Benchmark historical prices.
        sorting_columns: Columns to sort for each returned dataframe.

    Returns:
        DataFrame comparing asset and benchmark percentage gains.
    """
    assets_vs_benchmark = pd.DataFrame(
        {
            "ticker_asset": [],
            "curr_perc_gain_asset": [],
            "curr_perc_gain_benchmark": [],
            "position_status": [],
        },
    )

    for _, group in portfolio_model.groupby("ticker_asset"):
        group = benchmark_prices[  # noqa: PLW2901
            [
                "date",
                "ticker_benchmark",
                "split_benchmark",
                "close_unadj_local_currency_benchmark",
            ]
        ].merge(
            group[
                [
                    "date",
                    "ticker_asset",
                    "split_asset",
                    "close_unadj_local_currency_asset",
                    "trans_qty_asset",
                    "trans_val_asset",
                    "curr_qty_asset",
                    "curr_val_asset",
                ]
            ],
            how="left",
            on=["date"],
        )

        group = _simulate_benchmark_proportional(group)  # noqa: PLW2901

        group = utils.calc_curr_qty(  # noqa: PLW2901
            group,
            PositionType.BENCHMARK,
        )

        group = utils.calc_curr_val(  # noqa: PLW2901
            group,
            PositionType.BENCHMARK,
            sorting_columns=[{"columns": ["ticker_benchmark", "date"], "ascending": [True, False]}],
        )

        percent_gain_benchmark = utils.calc_simple_return_daily(
            group,
            PositionType.BENCHMARK,
            sorting_columns=[{"columns": ["date"], "ascending": [False]}],
        ).drop(columns=["curr_val_benchmark", "trans_val_benchmark", "money_out", "money_in"])

        percent_gain_asset = utils.calc_simple_return_daily(
            group,
            PositionType.ASSET,
            sorting_columns=[{"columns": ["date"], "ascending": [False]}],
        ).drop(columns=["curr_val_asset", "trans_val_asset", "money_out", "money_in"])

        assets_vs_benchmark.loc[len(assets_vs_benchmark)] = [
            group.iloc[0]["ticker_asset"],
            percent_gain_asset.iloc[0]["curr_perc_gain_asset"],
            percent_gain_benchmark.iloc[0]["curr_perc_gain_benchmark"],
            PositionStatus.OPEN.value
            if group["curr_qty_asset"].iloc[0]
            else PositionStatus.CLOSED.value,
        ]

    return assets_vs_benchmark.assign(
        diff=assets_vs_benchmark["curr_perc_gain_asset"]
        - assets_vs_benchmark["curr_perc_gain_benchmark"]
    )


def _simulate_benchmark_absolute(
    benchmark: pd.DataFrame,
    portfolio_data: PortfolioData,
) -> pd.DataFrame:
    """Model the benchmark as if the same transaction value purchased of an asset of the portfolio
    was purchased of the benchmark (in absoulte value).

    Args:
        benchmark: Benchmark historical data.
        portfolio_data: Transactions history and other portfolio data.

    Returns:
        Dataframe with the simulated trans_qty_benchmark.
    """
    return benchmark.merge(
        portfolio_data.transactions[["date", "trans_qty_asset", "trans_val_asset"]],
        how="left",
        on=["date"],
    ).assign(
        trans_val_asset=lambda df: df["trans_val_asset"].fillna(0),
        trans_qty_asset=lambda df: df["trans_qty_asset"].fillna(0),
        trans_qty_benchmark=lambda df: -df["trans_val_asset"]
        / df["close_unadj_local_currency_benchmark"],
    )


def _simulate_benchmark_proportional(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Simulate what would happen to benchmark if it was purchased/sold the same way as the asset
    in a proportional manner. Example: if curr_qty_asset is 100 and we buy 20 more, benchmark
    quantity is also increase by 20% (for example, from 60 to 72). If then 120 shares are sold
    (100%), 72 shares of benchmark are also sold (100%).

    Args:
        df: Dataframe with transaction history of asset and Yahoo finance prices for asset and
        benchmark.

    Returns:
        Dataframe with trans_qty_benchmark and trans_val_benchmark.
    """
    if not df["date"].is_monotonic_decreasing:
        raise UnsortedError

    (
        split_benchmark,
        trans_qty_asset,
        trans_val_asset,
        curr_qty_asset,
        close_unadj_local_currency_benchmark,
        split_asset,
    ) = (
        df["split_benchmark"].to_numpy(),
        df["trans_qty_asset"].to_numpy(),
        df["trans_val_asset"].to_numpy(),
        df["curr_qty_asset"].to_numpy(),
        df["close_unadj_local_currency_benchmark"].to_numpy(),
        df["split_asset"].to_numpy(),
    )

    trans_qty_benchmark = np.zeros(df_dim := len(split_benchmark), dtype=np.float64)
    latest_curr_qty_benchmark = 0
    ever_purchased = False

    for i in range(df_dim):
        latest_curr_qty_benchmark *= split_benchmark[~i]

        if not ever_purchased and trans_qty_asset[~i] != 0:
            trans_qty_benchmark[~i] = (
                -trans_val_asset[~i] / close_unadj_local_currency_benchmark[~i]
            )
            latest_curr_qty_benchmark += trans_qty_benchmark[~i]
            ever_purchased = True

        elif trans_qty_asset[~i] != 0:
            yesterdas_curr_qty = curr_qty_asset[~i + 1] * split_asset[~i]
            trans_qty_benchmark[~i] = (
                (trans_qty_asset[~i] + yesterdas_curr_qty) / yesterdas_curr_qty - 1
            ) * latest_curr_qty_benchmark
            latest_curr_qty_benchmark += trans_qty_benchmark[~i]

            if not latest_curr_qty_benchmark:
                ever_purchased = False

    return df.assign(
        trans_qty_benchmark=trans_qty_benchmark,
        trans_val_benchmark=-close_unadj_local_currency_benchmark * trans_qty_benchmark,
    )
