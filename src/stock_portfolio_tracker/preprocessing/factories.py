"""Factory functions for creating data API instances."""

from stock_portfolio_tracker.utils import DataApiType

from ._interfaces import DataApi, YahooFinanceApi


def create_data_api(data_api_type: DataApiType) -> DataApi:
    """Factory function to create a DataApi instance based on the specified type.

    Args:
        data_api_type (str): The type of API to create. Currently supports 'yahoo'.

    Returns:
        DataApi: An instance of the specified DataApi type.
    """
    match data_api_type:
        case DataApiType.YAHOO_FINANCE.value:
            return YahooFinanceApi()
        case DataApiType.TESTING.value:
            return "TODO"
        case _:
            msg = f"Unsupported API type: {data_api_type}"
            raise ValueError(msg)
