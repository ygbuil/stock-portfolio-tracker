"""Main module to execute the project."""

import modelling
import preprocessing
import reporting


def main() -> None:
    """Execute the project end to end."""
    portfolio_data, stock_prices, benchmarks = preprocessing.preprocess()

    stock_portfolio_value_evolution, benchmark_value_evolution = modelling.model_data(
        portfolio_data,
        benchmarks,
        stock_prices,
    )

    reporting.generate_report(stock_portfolio_value_evolution, benchmark_value_evolution)


if __name__ == "__main__":
    main()
