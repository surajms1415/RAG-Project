import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.router import api_router
from src.app.core.config import get_settings
from src.app.core.database import check_database_health, run_migrations
from src.app.core.exceptions import register_exception_handlers
from src.app.core.logging import setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL, json_logs=settings.LOG_JSON)
    logger.info(f"Starting {settings.APP_NAME} [Environment: {settings.APP_ENV}]")

    # Validate database connectivity on startup
    db_health = check_database_health()
    if db_health["status"] == "up":
        logger.info(
            f"Database connected successfully ({db_health['dialect']}) in {db_health['latency_ms']}ms"
        )
        if settings.AUTO_APPLY_MIGRATIONS:
            try:
                run_migrations()
            except Exception as e:
                logger.error(f"Migration auto-run failed: {e}")
    else:
        logger.warning(f"Database connectivity check failed on startup: {db_health['error']}")

    yield

    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global Exception Handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(api_router)

    return app


app = create_application()
