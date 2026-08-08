"""
Prompt Builder for AI Business Analyst.

Constructs modular system prompts, user query contexts, and structured report prompts
incorporating business metrics, EDA summaries, and ML model outputs.
"""

import json
from typing import Any, Dict, Optional


class PromptBuilder:
    """Modular prompt builder for LLM context injection."""

    def __init__(self):
        self.system_persona = (
            "You are the Lead AI Business Analyst for the Customer Intelligence Platform. "
            "You provide data-driven, strategic, and actionable enterprise insights based strictly "
            "on authoritative platform analytics, EDA findings, Customer Feature Store statistics, "
            "and ML model outputs (Customer Segmentation, CLV Prediction, Repeat Purchase Propensity). "
            "Maintain a professional, executive tone. Format responses cleanly using Markdown headers, "
            "bullet points, and financial/operational metrics."
        )

    def build_system_prompt(self) -> str:
        return self.system_persona

    def build_question_prompt(self, question: str, context: Dict[str, Any]) -> str:
        context_str = json.dumps(context, indent=2)
        return (
            f"--- BUSINESS CONTEXT METRICS ---\n"
            f"```json\n{context_str}\n```\n\n"
            f"--- USER QUESTION ---\n"
            f"{question}\n\n"
            f"Please answer the user's question accurately using the business context provided above."
        )

    def build_executive_summary_prompt(self, context: Dict[str, Any]) -> str:
        context_str = json.dumps(context, indent=2)
        return (
            f"--- FULL PLATFORM ANALYTICS CONTEXT ---\n"
            f"```json\n{context_str}\n```\n\n"
            f"Please generate a comprehensive Executive Summary Report covering:\n"
            f"1. Executive Financial Overview (Total Revenue, AOV, Order Volume)\n"
            f"2. Customer Demographics & Segmentation Breakdown\n"
            f"3. Delivery & Operational SLA Performance\n"
            f"4. Predictive Machine Learning Insights (CLV & Repeat Purchase Propensity)\n"
            f"5. Top Strategic Business Recommendations"
        )

    def build_weekly_report_prompt(self, context: Dict[str, Any]) -> str:
        context_str = json.dumps(context, indent=2)
        return (
            f"--- WEEKLY BUSINESS CONTEXT ---\n"
            f"```json\n{context_str}\n```\n\n"
            f"Please generate a Weekly Business Performance Report analyzing weekly/monthly trends, "
            f"revenue concentration, logistics bottleneck risks, and customer retention metrics."
        )

    def build_customer_report_prompt(self, customer_id: str, customer_features: Dict[str, Any]) -> str:
        features_str = json.dumps(customer_features, indent=2)
        return (
            f"--- CUSTOMER PROFILE & ML PREDICTIONS ---\n"
            f"Customer ID: {customer_id}\n"
            f"```json\n{features_str}\n```\n\n"
            f"Please generate an in-depth AI Customer Intelligence Report detailing:\n"
            f"- Customer Demographic Profile & Value Tier\n"
            f"- RFM & Purchase Behavior Analysis\n"
            f"- Assigned Segment Cluster & Business Persona\n"
            f"- Predicted CLV & Repeat Purchase Propensity\n"
            f"- Recommended Targeted Marketing / Retention Strategy"
        )

    def build_category_report_prompt(self, category: str, category_metrics: Dict[str, Any]) -> str:
        metrics_str = json.dumps(category_metrics, indent=2)
        return (
            f"--- PRODUCT CATEGORY METRICS ---\n"
            f"Category: {category}\n"
            f"```json\n{metrics_str}\n```\n\n"
            f"Please generate an AI Product Category Performance Report detailing:\n"
            f"- Revenue & Order Volume Performance\n"
            f"- Pricing & Average Order Value Dynamics\n"
            f"- Customer Satisfaction & Review Ratings\n"
            f"- Logistics & Freight Cost Efficiency\n"
            f"- Category Growth Opportunities & Recommendations"
        )
