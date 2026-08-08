"""
Pydantic v2 schemas for AI Business Analyst REST API.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class AIQuestionRequest(BaseModel):
    question: str = Field(..., description="Natural language business question", example="What is our total revenue and top state density?")


class AIQuestionResponse(BaseModel):
    question: str
    answer: str


class AICustomerReportRequest(BaseModel):
    customer_id: str = Field(..., description="Customer unique ID or customer ID", example="00012a2504309823e6e38064373a51d2")


class AICustomerReportResponse(BaseModel):
    customer_id: str
    report: str


class AICategoryReportRequest(BaseModel):
    category: str = Field(..., description="Product category name", example="bed_bath_table")


class AICategoryReportResponse(BaseModel):
    category: str
    report: str


class AIExecutiveSummaryResponse(BaseModel):
    title: str = "Executive Business Summary Report"
    summary: str
