from enum import Enum


class TwrFreq(Enum):
    YEARLY = "yearly"
    ALL = "all"


class PositionType(Enum):
    ASSET = "asset"
    PORTFOLIO = "portfolio"
    BENCHMARK = "benchmark"
