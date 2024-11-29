"""Module related to multithreading functionalities."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


def multithreader(func: Callable, args: list[tuple[Any]]) -> list[Any]:
    """Spawns multiple threads in parallel, efective for I/O bount operations such as API calls.

    Args:
        func: Function to parallelize.
        args: Arguments for the function, for each thread:
            [("NVDA", 01-01-2020, 01-01-2024), ("PYPL", 01-01-2020, 01-01-2024), ...]

    Returns:
        List with the result of each function.
    """
    result = []

    with ThreadPoolExecutor() as executor:
        # create a list of tasks to be submitted to the Tread Pool
        futures = [executor.submit(func, *curr_args) for curr_args in args]

        # append tasks to result as they are being completed
        for future in as_completed(futures):
            result.append(future.result())  # noqa: PERF401

    return result
