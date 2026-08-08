"""
FastAPI REST API router for AI Business Analyst endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.ai import (
    AICategoryReportRequest,
    AICategoryReportResponse,
    AICustomerReportRequest,
    AICustomerReportResponse,
    AIExecutiveSummaryResponse,
    AIQuestionRequest,
    AIQuestionResponse,
)
from app.services.ai_service import AIService, get_ai_service

router = APIRouter(tags=["AI Analyst"])


@router.post("/ask", response_model=AIQuestionResponse, summary="Answer a business question")
def ask_question(
    payload: AIQuestionRequest,
    service: AIService = Depends(get_ai_service),
):
    """
    Accepts a natural language business question and returns an AI-generated answer.
    """
    try:
        ans = service.ask(payload.question)
        return AIQuestionResponse(question=payload.question, answer=ans)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing AI question: {str(e)}",
        )


@router.post("/customer-report", response_model=AICustomerReportResponse, summary="Generate AI Customer Report")
def get_customer_report(
    payload: AICustomerReportRequest,
    service: AIService = Depends(get_ai_service),
):
    """
    Generates a detailed AI customer profile report incorporating RFM, Segment, CLV, and Repeat Propensity.
    """
    try:
        report = service.get_customer_report(payload.customer_id)
        return AICustomerReportResponse(customer_id=payload.customer_id, report=report)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating customer report: {str(e)}",
        )


@router.post("/category-report", response_model=AICategoryReportResponse, summary="Generate AI Product Category Report")
def get_category_report(
    payload: AICategoryReportRequest,
    service: AIService = Depends(get_ai_service),
):
    """
    Generates an AI performance report for a specified product category.
    """
    try:
        report = service.get_category_report(payload.category)
        return AICategoryReportResponse(category=payload.category, report=report)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating category report: {str(e)}",
        )


@router.get("/executive-summary", response_model=AIExecutiveSummaryResponse, summary="Get Executive Business Summary")
def get_executive_summary(
    service: AIService = Depends(get_ai_service),
):
    """
    Returns an Executive Business Summary Report compiling all platform analytics and model outputs.
    """
    try:
        summary = service.get_executive_summary()
        return AIExecutiveSummaryResponse(summary=summary)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating executive summary: {str(e)}",
        )
