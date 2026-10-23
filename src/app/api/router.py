from fastapi import APIRouter
from src.app.api.routes import documents, health, jobs, rag

api_router = APIRouter()

# Root health check endpoint (/health)
api_router.include_router(health.router)

# Versioned API endpoints (/api/v1/...)
api_router.include_router(documents.router, prefix="/api/v1")
api_router.include_router(jobs.router, prefix="/api/v1")
api_router.include_router(rag.router, prefix="/api/v1")
