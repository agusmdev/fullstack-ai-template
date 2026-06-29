"""Circuit breaker and retry patterns for external service calls.

This module provides utilities for resilient external API interactions
using the tenacity library's retry patterns.
"""

from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator factory for exponential backoff retries on external calls.

    Args:
        max_attempts: Maximum number of retry attempts.
        base_delay: Initial delay between retries in seconds.
        max_delay: Maximum delay between retries in seconds.

    Returns:
        A decorator that wraps functions with retry logic.

    Example:
        @retry_with_backoff(max_attempts=3)
        async def fetch_external_data(url: str) -> dict:
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        import functools

        import tenacity

        @tenacity.retry(
            stop=tenacity.stop_after_attempt(max_attempts),
            wait=tenacity.wait_exponential(multiplier=base_delay, max=max_delay),
            retry=tenacity.retry_if_exception_type((ConnectionError, TimeoutError)),
            reraise=True,
        )
        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> T:
            return func(*args, **kwargs)

        return wrapper

    return decorator
