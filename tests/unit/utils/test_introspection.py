"""Tests for introspection utilities."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, ParamSpec, TypeVar

from apps.api.utils.introspection import supports_param

if TYPE_CHECKING:
    from collections.abc import Callable

P = ParamSpec("P")
R = TypeVar("R")


def simple_function(a: int, b: str) -> None:
    """Simple function with typed parameters."""
    pass


def function_with_defaults(x: int, y: str = "default") -> None:
    """Function with default parameters."""
    pass


def function_with_args(*args: int) -> None:
    """Function with *args."""
    pass


def function_with_kwargs(**kwargs: str) -> None:
    """Function with **kwargs."""
    pass


def function_with_both(*args: int, **kwargs: str) -> None:
    """Function with both *args and **kwargs."""
    pass


def decorated_function(value: int) -> int:
    """Decorator target for testing."""
    return value * 2


@functools.lru_cache(maxsize=32)
def cached_function(param: str) -> str:
    """Function decorated with lru_cache."""
    return param.upper()


def wrapper_decorator(func: Callable[P, R]) -> Callable[P, R]:
    """Custom decorator that preserves signature with functools.wraps."""

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return func(*args, **kwargs)

    return wrapper


@wrapper_decorator
def decorated_with_wraps(x: int, y: str) -> None:
    """Function decorated with wrapper that uses functools.wraps."""
    pass


class TestSupportsParam:
    """Tests for supports_param function."""

    def test_simple_function_has_param(self) -> None:
        """Test that simple function parameters are detected."""
        assert supports_param(simple_function, "a") is True
        assert supports_param(simple_function, "b") is True

    def test_simple_function_missing_param(self) -> None:
        """Test that missing parameters return False."""
        assert supports_param(simple_function, "c") is False
        assert supports_param(simple_function, "missing") is False

    def test_function_with_defaults(self) -> None:
        """Test functions with default parameter values."""
        assert supports_param(function_with_defaults, "x") is True
        assert supports_param(function_with_defaults, "y") is True
        assert supports_param(function_with_defaults, "z") is False

    def test_function_with_args(self) -> None:
        """Test function with *args parameter."""
        assert supports_param(function_with_args, "args") is True
        assert supports_param(function_with_args, "other") is False

    def test_function_with_kwargs(self) -> None:
        """Test function with **kwargs parameter."""
        assert supports_param(function_with_kwargs, "kwargs") is True
        assert supports_param(function_with_kwargs, "other") is False

    def test_function_with_both_varargs(self) -> None:
        """Test function with both *args and **kwargs."""
        assert supports_param(function_with_both, "args") is True
        assert supports_param(function_with_both, "kwargs") is True
        assert supports_param(function_with_both, "missing") is False

    def test_decorated_function_with_wraps(self) -> None:
        """Test decorated function that uses functools.wraps."""
        # functools.wraps preserves the original signature
        assert supports_param(decorated_with_wraps, "x") is True
        assert supports_param(decorated_with_wraps, "y") is True
        assert supports_param(decorated_with_wraps, "z") is False

    def test_cached_function_signature(self) -> None:
        """Test that lru_cache decorated functions are inspectable."""
        # lru_cache wraps functions but preserves signature
        assert supports_param(cached_function, "param") is True
        assert supports_param(cached_function, "missing") is False

    def test_builtin_function_signature(self) -> None:
        """Test that built-in functions have inspectable signatures in Python 3.8+."""
        # In Python 3.8+, many built-in functions have inspect-able signatures
        # print has signature: print(*values, sep=' ', end='\n', file=None, flush=False)
        assert supports_param(print, "sep") is True
        assert supports_param(print, "end") is True
        assert supports_param(print, "file") is True

        # len doesn't have named parameters (all positional-only)
        # but we can verify it has a signature that can be inspected
        import inspect

        try:
            inspect.signature(len)
            # If we can get a signature, supports_param should not crash
            # (even if it returns False for missing param names)
            assert supports_param(len, "nonexistent") is False
        except (TypeError, ValueError):
            # If len doesn't have inspectable signature, that's also valid
            pass

    def test_builtin_method_signature(self) -> None:
        """Test that built-in methods have inspectable signatures in Python 3.8+."""
        # In Python 3.8+, built-in methods are also inspectable
        # str.upper has signature: upper(self, /)
        assert supports_param(str.upper, "self") is True

        # list.append has signature: append(self, object, /)
        assert supports_param(list.append, "self") is True
        assert supports_param(list.append, "object") is True

    def test_lambda_function(self) -> None:
        """Test lambda functions are inspectable."""
        lambda_func = lambda x, y: x + y  # noqa: E731
        assert supports_param(lambda_func, "x") is True
        assert supports_param(lambda_func, "y") is True
        assert supports_param(lambda_func, "z") is False

    def test_class_method(self) -> None:
        """Test class methods are inspectable."""

        class Example:
            def method(self, param: str) -> None:
                pass

        assert supports_param(Example.method, "self") is True
        assert supports_param(Example.method, "param") is True
        assert supports_param(Example.method, "missing") is False

    def test_static_method(self) -> None:
        """Test static methods are inspectable."""

        class Example:
            @staticmethod
            def static_method(value: int) -> int:
                return value * 2

        assert supports_param(Example.static_method, "value") is True
        assert supports_param(Example.static_method, "missing") is False

    def test_class_method_decorator(self) -> None:
        """Test classmethod decorated methods."""

        class Example:
            @classmethod
            def class_method(cls, param: str) -> None:
                pass

        assert supports_param(Example.class_method, "param") is True
        assert supports_param(Example.class_method, "missing") is False

    def test_cache_is_used(self) -> None:
        """Test that LRU cache is actually being used."""
        # Clear cache to start fresh
        supports_param.cache_clear()

        # First call - cache miss
        result1 = supports_param(simple_function, "a")
        cache_info1 = supports_param.cache_info()
        assert result1 is True
        assert cache_info1.hits == 0
        assert cache_info1.misses == 1

        # Second call - cache hit
        result2 = supports_param(simple_function, "a")
        cache_info2 = supports_param.cache_info()
        assert result2 is True
        assert cache_info2.hits == 1
        assert cache_info2.misses == 1

        # Different parameter - cache miss
        result3 = supports_param(simple_function, "b")
        cache_info3 = supports_param.cache_info()
        assert result3 is True
        assert cache_info3.hits == 1
        assert cache_info3.misses == 2

    def test_cache_thread_safety(self) -> None:
        """Test that cache is thread-safe (lru_cache guarantees this)."""
        import threading

        results: list[bool] = []
        errors: list[Exception] = []

        def worker() -> None:
            try:
                # Each thread checks the same parameter
                result = supports_param(simple_function, "a")
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Clear cache
        supports_param.cache_clear()

        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify no errors
        assert len(errors) == 0, f"Thread errors: {errors}"

        # Verify all results are True
        assert len(results) == 10
        assert all(results)

        # Verify cache was hit multiple times (proves thread safety)
        cache_info = supports_param.cache_info()
        assert cache_info.hits > 0

    def test_signature_inspection_failure_with_callable(self) -> None:
        """Test graceful handling when signature inspection fails."""

        class NonInspectableCallable:
            """Callable that raises ValueError on signature inspection."""

            def __call__(self, *args: object, **kwargs: object) -> None:
                pass

            def __signature__(self) -> None:
                raise ValueError("Cannot inspect signature")

        callable_obj = NonInspectableCallable()
        # Should return False instead of raising
        assert supports_param(callable_obj, "anything") is False

    def test_async_function(self) -> None:
        """Test async functions are inspectable."""

        async def async_function(param: str) -> None:
            pass

        assert supports_param(async_function, "param") is True
        assert supports_param(async_function, "missing") is False

    def test_generator_function(self) -> None:
        """Test generator functions are inspectable."""

        def generator_function(param: str):
            yield param

        assert supports_param(generator_function, "param") is True
        assert supports_param(generator_function, "missing") is False

    def test_edge_case_empty_string_param(self) -> None:
        """Test checking for empty string parameter name."""

        def func_with_normal_params(a: int) -> None:
            pass

        # Empty string is a valid parameter name to check for
        assert supports_param(func_with_normal_params, "") is False

    def test_unicode_parameter_names(self) -> None:
        """Test functions with unicode parameter names."""
        # Python allows unicode identifiers
        # Use a dict to capture the function from exec
        namespace: dict[str, object] = {}
        exec("def func_unicode(παράμετρος: str) -> None: pass", namespace)
        func_unicode = namespace["func_unicode"]

        assert supports_param(func_unicode, "παράμετρος") is True
        assert supports_param(func_unicode, "other") is False


class TestCacheConfiguration:
    """Tests for cache configuration."""

    def test_cache_maxsize(self) -> None:
        """Test that cache has correct maxsize."""
        # Clear cache
        supports_param.cache_clear()

        # Check cache info
        cache_info = supports_param.cache_info()
        assert cache_info.maxsize == 128

    def test_cache_can_be_cleared(self) -> None:
        """Test that cache can be cleared."""
        # Add some entries
        supports_param(simple_function, "a")
        supports_param(simple_function, "b")

        cache_info_before = supports_param.cache_info()
        assert cache_info_before.currsize > 0

        # Clear cache
        supports_param.cache_clear()

        cache_info_after = supports_param.cache_info()
        assert cache_info_after.currsize == 0
        assert cache_info_after.hits == 0
        assert cache_info_after.misses == 0
