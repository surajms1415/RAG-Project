from fastapi import APIRouter, Response, status
from src.app.core.config import get_settings
from src.app.core.database import check_database_health
from src.app.schemas.health import DependencyHealth, HealthResponse

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/health", response_model=HealthResponse)
def health_check(response: Response) -> HealthResponse:
    """Evaluates connectivity to system dependencies and reports overall health."""
    db_result = check_database_health()

    db_health = DependencyHealth(
        status=db_result["status"],
        latency_ms=db_result["latency_ms"],
        dialect=db_result["dialect"],
        error=db_result["error"],
    )

    is_healthy = db_health.status == "up"

    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="healthy" if is_healthy else "unhealthy",
        environment=settings.APP_ENV,
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        dependencies={
            "database": db_health,
        },
    )
