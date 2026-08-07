from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from app.api.router import api_router
from app.api.v1.health import router as health_router
from app.core.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager for startup and shutdown events.
    """
    setup_logging()
    logger.info(f"Starting {settings.PROJECT_NAME} in {settings.ENVIRONMENT} mode...")
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Direct root /health route handler
app.include_router(health_router, tags=["Health"])

# Versioned API routes under /api/v1
app.include_router(api_router, prefix=settings.API_V1_STR)
