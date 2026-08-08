"""
AI Analyst Service.

Service layer wrapping BusinessAnalyst with request/response logging
and dependency injection helper for FastAPI endpoints.
"""

from typing import Any, Dict, Optional
from loguru import logger

from app.ai.analyst import BusinessAnalyst


class AIService:
    """Service wrapping AI Business Analyst functions."""

    def __init__(self, analyst: Optional[BusinessAnalyst] = None):
        self.analyst = analyst or BusinessAnalyst()

    def ask(self, question: str) -> str:
        logger.info(f"AIService.ask question: '{question}'")
        answer = self.analyst.answer_question(question)
        logger.info(f"AIService.ask answer generated ({len(answer)} chars)")
        return answer

    def get_customer_report(self, customer_id: str) -> str:
        logger.info(f"AIService.get_customer_report for customer_id: '{customer_id}'")
        report = self.analyst.generate_customer_report(customer_id)
        logger.info(f"AIService.get_customer_report generated ({len(report)} chars)")
        return report

    def get_category_report(self, category: str) -> str:
        logger.info(f"AIService.get_category_report for category: '{category}'")
        report = self.analyst.generate_category_report(category)
        logger.info(f"AIService.get_category_report generated ({len(report)} chars)")
        return report

    def get_executive_summary(self) -> str:
        logger.info("AIService.get_executive_summary requested.")
        summary = self.analyst.generate_executive_summary()
        logger.info(f"AIService.get_executive_summary generated ({len(summary)} chars)")
        return summary


# Dependency injection singleton
_ai_service_instance: Optional[AIService] = None


def get_ai_service() -> AIService:
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance
