"""Decorators."""

import time
from collections.abc import Callable
from typing import Any

import pandas as pd
from loguru import logger


def sort_at_end() -> Callable[..., Any]:
    """Sort the output dataframe of functions."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame | list[pd.DataFrame]:
            sorting_columns = kwargs["sorting_columns"]
            dfs = func(*args, **kwargs)

            output = []
            single_df = isinstance(dfs, pd.DataFrame)

            for df, sorting_column in zip(
                (dfs,) if single_df else dfs,
                sorting_columns,
                strict=False,
            ):
                output.append(
                    df.sort_values(
                        by=sorting_column["columns"],
                        ascending=sorting_column["ascending"],
                    ).reset_index(drop=True),
                )

            return output[0] if single_df else output

        return wrapper

    return decorator


def timer(func: Callable[..., Any]) -> Callable[..., Any]:
    """Count the time a function takes to execute."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        logger.info(f"Total execution time: {(end_time - start_time):.1f} seconds.")
        return result

    return wrapper
