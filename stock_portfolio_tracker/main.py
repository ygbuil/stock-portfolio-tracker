"""Main module to execute the project."""

import modelling
import preprocessing
import reporting
from loguru import logger


def main() -> None:
    """Execute the project end to end."""
    logger.info("Start of execution.")
    config, portfolio_data, asset_prices, benchmarks = preprocessing.preprocess()

    (
        asset_portfolio_value_evolution,
        asset_portfolio_current_positions,
        benchmark_value_evolution,
    ) = modelling.model_data(
        portfolio_data,
        benchmarks,
        asset_prices,
    )

    reporting.generate_reports(
        config,
        asset_portfolio_value_evolution,
        asset_portfolio_current_positions,
        benchmark_value_evolution,
    )

    logger.info("End of execution.")


if __name__ == "__main__":
    main()
