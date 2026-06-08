import time
import functools

def ttl_cache(seconds: float = 60.0):
    """
    In-memory cache decorator for async functions with Time-To-Live (TTL).
    Includes a .cache_clear() method to clear cached values.
    """
    def decorator(func):
        cache_data = {}

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Simple argument-based key serialization
            key = (args, frozenset(kwargs.items()))
            now = time.time()
            
            if key in cache_data:
                val, expiry = cache_data[key]
                if now < expiry:
                    return val
            
            result = await func(*args, **kwargs)
            cache_data[key] = (result, now + seconds)
            return result

        def cache_clear():
            cache_data.clear()

        wrapper.cache_clear = cache_clear
        return wrapper
    return decorator
