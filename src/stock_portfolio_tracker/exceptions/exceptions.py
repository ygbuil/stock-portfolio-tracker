"""Custom exceptions."""


class YahooFinanceError(Exception):
    """Error with the Yahoo Finance API."""

    def __init__(self: "YahooFinanceError", msg: None | str = None) -> None:
        """Provide the error message."""
        super().__init__(msg or "Something went wrong retrieving Yahoo Finance.")


class UnsortedError(Exception):
    """Error with data sorting."""

    def __init__(self: "UnsortedError", msg: None | str = None) -> None:
        """Provide the error message."""
        super().__init__(msg or "The data is not sorted as expected.")
