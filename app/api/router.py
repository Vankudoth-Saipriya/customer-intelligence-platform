from fastapi import APIRouter
from app.api.v1 import health, ml

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
