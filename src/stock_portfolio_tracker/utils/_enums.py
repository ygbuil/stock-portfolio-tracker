from enum import Enum


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
