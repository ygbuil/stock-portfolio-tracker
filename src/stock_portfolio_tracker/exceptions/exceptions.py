"""Custom exceptions."""


class YahooFinanceError(Exception):
    """Error with the Yahoo Finance API."""


class UnsortedError(Exception):
    """The data is not sorted as expected."""

    def __init__(self: "UnsortedError", message: None | str = None) -> None:
        """Provide the error message."""
        super().__init__(message or "The data is not sorted as expected.")
