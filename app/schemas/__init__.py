"""
Schemas Package.
"""

from app.schemas.ai import (
    AICategoryReportRequest,
    AICategoryReportResponse,
    AICustomerReportRequest,
    AICustomerReportResponse,
    AIExecutiveSummaryResponse,
    AIQuestionRequest,
    AIQuestionResponse,
)
from app.schemas.ml import (
    CLVResponse,
    CustomerFeaturePayload,
    MLHealthResponse,
    ModelsInfoResponse,
    RepeatPurchaseResponse,
    SegmentationResponse,
)

__all__ = [
    "CustomerFeaturePayload",
    "SegmentationResponse",
    "CLVResponse",
    "RepeatPurchaseResponse",
    "ModelsInfoResponse",
    "MLHealthResponse",
    "AIQuestionRequest",
    "AIQuestionResponse",
    "AICustomerReportRequest",
    "AICustomerReportResponse",
    "AICategoryReportRequest",
    "AICategoryReportResponse",
    "AIExecutiveSummaryResponse",
]
