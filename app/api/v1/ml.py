"""
ML Inference API v1 Endpoints.
"""

from fastapi import APIRouter, Depends, status
from loguru import logger

from app.schemas.ml import (
    CLVResponse,
    CustomerFeaturePayload,
    MLHealthResponse,
    ModelsInfoResponse,
    RepeatPurchaseResponse,
    SegmentationResponse,
)
from app.services.ml_service import MLService, get_ml_service

router = APIRouter()


@router.post(
    "/segment",
    response_model=SegmentationResponse,
    status_code=status.HTTP_200_OK,
    summary="Customer Segmentation Inference",
    description="Assigns a customer payload to a segmented cluster using trained KMeans model.",
)
def predict_segment(
    payload: CustomerFeaturePayload,
    ml_service: MLService = Depends(get_ml_service),
) -> SegmentationResponse:
    """
    POST /api/v1/ml/segment
    """
    logger.info("Received POST /api/v1/ml/segment inference request")
    return ml_service.predict_segment(payload)


@router.post(
    "/clv",
    response_model=CLVResponse,
    status_code=status.HTTP_200_OK,
    summary="Customer Lifetime Value (CLV) Prediction",
    description="Predicts expected Customer Lifetime Value (total revenue) using trained Random Forest Regressor.",
)
def predict_clv(
    payload: CustomerFeaturePayload,
    ml_service: MLService = Depends(get_ml_service),
) -> CLVResponse:
    """
    POST /api/v1/ml/clv
    """
    logger.info("Received POST /api/v1/ml/clv inference request")
    return ml_service.predict_clv(payload)


@router.post(
    "/repeat-purchase",
    response_model=RepeatPurchaseResponse,
    status_code=status.HTTP_200_OK,
    summary="Repeat Purchase Propensity Prediction",
    description="Predicts repeat purchase propensity probability and binary classification.",
)
def predict_repeat_purchase(
    payload: CustomerFeaturePayload,
    ml_service: MLService = Depends(get_ml_service),
) -> RepeatPurchaseResponse:
    """
    POST /api/v1/ml/repeat-purchase
    """
    logger.info("Received POST /api/v1/ml/repeat-purchase inference request")
    return ml_service.predict_repeat_purchase(payload)


@router.get(
    "/models",
    response_model=ModelsInfoResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Available ML Models Information",
    description="Returns metadata, metrics, feature counts, and statuses for all trained ML models.",
)
def get_models_info(
    ml_service: MLService = Depends(get_ml_service),
) -> ModelsInfoResponse:
    """
    GET /api/v1/ml/models
    """
    logger.info("Received GET /api/v1/ml/models request")
    return ml_service.get_models_info()


@router.get(
    "/health",
    response_model=MLHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="ML Inference Service Health Check",
    description="Returns ML inference service health status, version, and loaded model availability.",
)
def get_ml_health(
    ml_service: MLService = Depends(get_ml_service),
) -> MLHealthResponse:
    """
    GET /api/v1/ml/health
    """
    logger.info("Received GET /api/v1/ml/health request")
    return ml_service.get_health()
