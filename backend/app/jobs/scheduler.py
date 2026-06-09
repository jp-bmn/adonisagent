"""
APScheduler-based in-process scheduler.
Runs Mon/Wed/Fri at 11:00 UTC (6:00 AM ET).
Monday also triggers the weekly digest send.

Started from main.py on application startup.
Full job implementations live in scraper_job.py (Task 6).
"""
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(timezone="UTC")


def _run_scraper_sync():
    """Sync wrapper for the async scraper job (APScheduler is sync)."""
    import asyncio
    try:
        # Import here to avoid circular imports at module load time
        from app.jobs.scraper_job import run_scraper_job
        asyncio.run(run_scraper_job())
    except Exception as e:
        logger.error(f"Scraper job failed: {e}")


def _run_monday_digest_sync():
    """Sync wrapper for Monday digest job."""
    import asyncio
    try:
        from app.jobs.scraper_job import run_monday_digest
        asyncio.run(run_monday_digest())
    except Exception as e:
        logger.error(f"Monday digest job failed: {e}")


def start_scheduler():
    """Register all cron jobs and start the scheduler. Called on app startup."""
    # Monday 11:00 UTC — scrape + send digest
    scheduler.add_job(
        _run_monday_digest_sync,
        CronTrigger(day_of_week="mon", hour=11, minute=0, timezone="UTC"),
        id="weekly-mon-digest",
        replace_existing=True,
    )
    # Wednesday 11:00 UTC — scrape only
    scheduler.add_job(
        _run_scraper_sync,
        CronTrigger(day_of_week="wed", hour=11, minute=0, timezone="UTC"),
        id="weekly-wed-scrape",
        replace_existing=True,
    )
    # Friday 11:00 UTC — scrape only
    scheduler.add_job(
        _run_scraper_sync,
        CronTrigger(day_of_week="fri", hour=11, minute=0, timezone="UTC"),
        id="weekly-fri-scrape",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started — Mon/Wed/Fri 11:00 UTC crons registered")


def stop_scheduler():
    """Gracefully shut down the scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler stopped")
