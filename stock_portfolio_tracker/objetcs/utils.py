"""Module to store various util objects."""

from typing import Callable

import pandas as pd


def sort_at_end() -> Callable:
    """Sort the output dataframe of functions, used as decorator."""

    def decorator(func: Callable) -> Callable:
        def wrapper(df: pd.DataFrame, *args, **kwargs) -> pd.DataFrame:
            sorting_columns = kwargs.get("sorting_columns")
            df = func(df, *args, **kwargs)

            return df.sort_values(
                by=sorting_columns["columns"],
                ascending=sorting_columns["ascending"],
            ).reset_index(drop=True)

        return wrapper

    return decorator
