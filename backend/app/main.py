"""
Adonis Account Intelligence API — FastAPI application entry point.

Health check: GET /
All endpoints mounted under /api/v1/
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.endpoints import (
    admin,
    classify,
    contacts,
    digests,
    export,
    hospitals,
    ingest,
    runs,
    signals,
    users,
    views,
)
from app.jobs.scheduler import start_scheduler, stop_scheduler

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Adonis Intelligence API starting up")
    start_scheduler()
    yield
    logger.info("Adonis Intelligence API shutting down")
    stop_scheduler()


# ---------------------------------------------------------------------------
# App init
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Adonis Account Intelligence API",
    description=(
        "Internal sales intelligence API. Monitors hospital news, "
        "classifies signals with AI, and delivers weekly Slack digests."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS — allow all origins in dev mode
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,
)


# ---------------------------------------------------------------------------
# Request logging middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)"
    )
    return response


# ---------------------------------------------------------------------------
# Global exception handler — never expose raw stack traces
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    
    # Notify Danielle via Slack in production (Task 16)
    try:
        from app.services.slack_service import send_dm
        from app.core.config import get_settings
        settings = get_settings()
        danielle_id = settings.slack_user_id_danielle
        if danielle_id and not danielle_id.startswith("PLACEHOLDER"):
            send_dm(
                slack_user_id=danielle_id,
                text=f"🚨 *Internal Server Error (500)* on `{request.method} {request.url.path}`\nError: `{str(exc)}`"
            )
    except Exception as slack_err:
        logger.error(f"Failed to notify Danielle via Slack: {slack_err}")

    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "adonis-intelligence-api"}


# ---------------------------------------------------------------------------
# API v1 routers
# ---------------------------------------------------------------------------
PREFIX = "/api/v1"

app.include_router(hospitals.router, prefix=PREFIX)
app.include_router(signals.router, prefix=PREFIX)
app.include_router(ingest.router, prefix=PREFIX)   # Michael's batch ingest
app.include_router(contacts.router, prefix=PREFIX)
app.include_router(digests.router, prefix=PREFIX)
app.include_router(views.router, prefix=PREFIX)
app.include_router(export.router, prefix=PREFIX)
app.include_router(runs.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)
app.include_router(classify.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
