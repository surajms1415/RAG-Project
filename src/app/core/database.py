import logging
import time
from typing import Any, Dict, Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import StaticPool, NullPool
from src.app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

Base = declarative_base()


def get_engine_args(db_url: str) -> Dict[str, Any]:
    """Returns suitable engine arguments based on dialect."""
    if db_url.startswith("sqlite"):
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool if ":memory:" in db_url else None,
        }
    return {
        "pool_size": settings.DATABASE_POOL_SIZE,
        "max_overflow": settings.DATABASE_MAX_OVERFLOW,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }


engine_kwargs = {k: v for k, v in get_engine_args(settings.DATABASE_URL).items() if v is not None}
engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_health() -> Dict[str, Any]:
    """Checks database connectivity by executing a lightweight query."""
    start_time = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "up",
            "latency_ms": latency_ms,
            "dialect": engine.dialect.name,
            "error": None,
        }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        logger.error(f"Database health check failed: {exc}", exc_info=True)
        return {
            "status": "down",
            "latency_ms": latency_ms,
            "dialect": engine.dialect.name,
            "error": str(exc),
        }


def run_migrations(alembic_cfg_path: str = "alembic.ini") -> bool:
    """Programmatically runs Alembic migrations up to head."""
    from alembic import command
    from alembic.config import Config

    try:
        logger.info("Executing database migrations...")
        cfg = Config(alembic_cfg_path)
        cfg.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.upgrade(cfg, "head")
        logger.info("Database migrations successfully applied.")
        return True
    except Exception as e:
        logger.error(f"Failed to execute database migrations: {e}", exc_info=True)
        raise
