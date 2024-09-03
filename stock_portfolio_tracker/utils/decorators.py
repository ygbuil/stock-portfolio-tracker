"""Module to store various util objects."""

import time
from typing import Any, Callable

import pandas as pd
from loguru import logger


def sort_at_end() -> Callable:
    """Sort the output dataframe of functions."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> tuple[pd.DataFrame]:
            sorting_columns = kwargs.get("sorting_columns")
            dfs = func(*args, **kwargs)

            # if only 1 df is returned
            if isinstance(dfs, pd.DataFrame):
                return dfs.sort_values(
                    by=sorting_columns[0]["columns"],
                    ascending=sorting_columns[0]["ascending"],
                ).reset_index(drop=True)

            # if more than 1 df is returned
            output = []
            for df, sorting_column in zip(dfs, sorting_columns):
                output.append(
                    df.sort_values(
                        by=sorting_column["columns"],
                        ascending=sorting_column["ascending"],
                    ).reset_index(drop=True),
                )

            return output

        return wrapper

    return decorator


def timer(func: Callable) -> Callable:
    """Count the time a function takes to execute."""

    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        logger.info(f"Total execution time: {(end_time - start_time):.1f} seconds.")
        return result

    return wrapper
