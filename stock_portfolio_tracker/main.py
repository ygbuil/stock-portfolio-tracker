"""Main module to execute the project."""

import modelling
import preprocessing
import reporting
from loguru import logger


def main() -> None:
    """Execute the project end to end."""
    logger.info("Start of execution.")
    portfolio_data, stock_prices, benchmarks = preprocessing.preprocess()

    stock_portfolio_value_evolution, benchmark_value_evolution = modelling.model_data(
        portfolio_data,
        benchmarks,
        stock_prices,
    )

    reporting.generate_reports(stock_portfolio_value_evolution, benchmark_value_evolution)

    logger.info("End of execution.")


if __name__ == "__main__":
    main()
