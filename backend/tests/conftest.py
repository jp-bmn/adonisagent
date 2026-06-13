"""
Pytest configuration for the Adonis backend.
"""
import pytest


# Mark all async tests automatically
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(autouse=True)
def clear_ttl_caches():
    from app.api.endpoints.runs import latest_run, system_status
    latest_run.cache_clear()
    system_status.cache_clear()
