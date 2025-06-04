from enum import Enum


class DataApiType(Enum):
    YAHOO_FINANCE = "yahoo_finance"
    TESTING = "testing"


class TwrFreq(Enum):
    YEARLY = "yearly"
    ALL = "all"


class PositionType(Enum):
    ASSET = "asset"
    PORTFOLIO = "portfolio"
    BENCHMARK = "benchmark"


class TransactionType(Enum):
    SALE = "Sale"
    PURCHASE = "Purchase"


class PositionStatus(Enum):
    OPEN = "open"
    CLOSED = "closed"
