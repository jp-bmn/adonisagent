import asyncio
import functools
import logging

logger = logging.getLogger(__name__)


def with_retry(max_attempts: int = 3, base_delay: float = 2.0):
    """
    Async exponential-backoff retry decorator.
    Apply to any async function that makes network calls (Claude API, Slack SDK).
    Do NOT apply to pure CPU functions like rules_engine().
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    delay *= 2  # exponential backoff
        return wrapper
    return decorator
