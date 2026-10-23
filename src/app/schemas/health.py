from typing import Dict, Optional
from pydantic import BaseModel, Field


class DependencyHealth(BaseModel):
    status: str = Field(description="Health status: 'up' or 'down'")
    latency_ms: Optional[float] = Field(default=None, description="Response time in milliseconds")
    dialect: Optional[str] = Field(default=None, description="Database dialect or service variant")
    error: Optional[str] = Field(default=None, description="Error detail if status is down")


class HealthResponse(BaseModel):
    status: str = Field(description="'healthy' if all critical dependencies are up, else 'unhealthy'")
    environment: str
    app_name: str
    version: str
    dependencies: Dict[str, DependencyHealth]
