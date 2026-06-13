"""
Test: GET / health check
"""
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health_check():
    """GET / should return 200 with the correct JSON payload."""
    # Override settings so the app starts without real env vars
    import os
    os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
    os.environ.setdefault("SUPABASE_KEY", "test-key")
    os.environ.setdefault("SLACK_BOT_TOKEN", "xoxb-test")
    os.environ.setdefault("SLACK_SIGNING_SECRET", "test-secret")
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic")
    os.environ.setdefault("INTERNAL_API_KEY", "test-internal")

    # Patch the scheduler so it doesn't actually start APScheduler in tests
    import app.jobs.scheduler as sched_module
    original_start = sched_module.start_scheduler
    original_stop = sched_module.stop_scheduler
    sched_module.start_scheduler = lambda: None
    sched_module.stop_scheduler = lambda: None

    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/")

    sched_module.start_scheduler = original_start
    sched_module.stop_scheduler = original_stop

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "adonis-intelligence-api"
