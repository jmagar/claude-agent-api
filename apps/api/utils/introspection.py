"""Runtime introspection utilities."""

import functools
import inspect
from collections.abc import Callable
from typing import ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


@functools.lru_cache(maxsize=128)
def supports_param(func: Callable[P, R], name: str) -> bool:
    """Check if a callable supports a specific parameter name.

    Uses LRU cache to avoid repeated signature introspection for the same
    function. Cache size of 128 is sufficient for typical API workloads.

    Args:
        func: Callable to inspect for parameter support.
        name: Parameter name to check for.

    Returns:
        True if the function signature includes the parameter name.
        False if parameter is not found or signature inspection fails.

    Example:
        >>> def example(a: int, b: str) -> None: pass
        >>> supports_param(example, "a")
        True
        >>> supports_param(example, "c")
        False
    """
    try:
        return name in inspect.signature(func).parameters
    except (TypeError, ValueError):
        # Signature inspection failed (e.g., built-in function, C extension)
        return False
