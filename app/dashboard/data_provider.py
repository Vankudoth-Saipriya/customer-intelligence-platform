"""
Dashboard Data Provider.

Cached data provider layer for Streamlit pages consuming EDA JSON artifacts,
ML Parquet prediction tables, and FastAPI ML inference endpoints.
Optimized for lazy artifact loading, column projections, and low memory usage.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
import requests
import streamlit as st

from app.services.ai_service import AIService, get_ai_service
from app.services.ml_service import MLService, get_ml_service

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
API_HOST = os.getenv("API_URL", "http://127.0.0.1:8000")
API_BASE_URL = f"{API_HOST}/api/v1/ml"
AI_API_BASE_URL = f"{API_HOST}/api/v1/ai"


@st.cache_resource
def get_cached_ml_service() -> MLService:
    """Cache singleton MLService resource in memory."""
    return get_ml_service()


@st.cache_resource
def get_cached_ai_service() -> AIService:
    """Cache singleton AIService resource in memory."""
    return get_ai_service()


@st.cache_data
def get_customer_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "customer_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def get_product_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "product_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def get_sales_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "sales_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def get_delivery_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "delivery_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def get_payment_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "payment_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def get_review_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "review_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def get_feature_store() -> pd.DataFrame:
    path = ARTIFACTS_DIR / "features" / "customer_feature_store.parquet"
    cols = ["customer_id", "customer_unique_id", "customer_age_days", "frequency_orders", "monetary_value", "recency_days", "customer_value_tier"]
    return pd.read_parquet(path, columns=cols)


@st.cache_data
def get_customer_segments() -> pd.DataFrame:
    path = ARTIFACTS_DIR / "ml" / "customer_segments.parquet"
    cols = ["customer_id", "customer_unique_id", "cluster_id", "cluster_description", "total_revenue"]
    return pd.read_parquet(path, columns=cols)


@st.cache_data
def get_clv_predictions() -> pd.DataFrame:
    path = ARTIFACTS_DIR / "ml" / "customer_clv_predictions.parquet"
    cols = ["customer_id", "customer_unique_id", "total_revenue", "predicted_clv", "customer_value_tier", "state", "frequency_orders"]
    return pd.read_parquet(path, columns=cols)


@st.cache_data
def get_repeat_predictions() -> pd.DataFrame:
    path = ARTIFACTS_DIR / "ml" / "repeat_purchase_predictions.parquet"
    cols = ["customer_id", "customer_unique_id", "repeat_customer", "repeat_propensity", "predicted_repeat_customer"]
    return pd.read_parquet(path, columns=cols)


def call_segment_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call POST /api/v1/ml/segment with fallback to cached MLService."""
    payload = feature_payload or {"customer_id": customer_id}
    try:
        res = requests.post(f"{API_BASE_URL}/segment", json=payload, timeout=2.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    from app.schemas.ml import CustomerFeaturePayload
    service = get_cached_ml_service()
    resp = service.predict_segment(CustomerFeaturePayload(**payload))
    return resp.model_dump()


def call_clv_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call POST /api/v1/ml/clv with fallback to cached MLService."""
    payload = feature_payload or {"customer_id": customer_id}
    try:
        res = requests.post(f"{API_BASE_URL}/clv", json=payload, timeout=2.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    from app.schemas.ml import CustomerFeaturePayload
    service = get_cached_ml_service()
    resp = service.predict_clv(CustomerFeaturePayload(**payload))
    return resp.model_dump()


def call_repeat_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call POST /api/v1/ml/repeat-purchase with fallback to cached MLService."""
    payload = feature_payload or {"customer_id": customer_id}
    try:
        res = requests.post(f"{API_BASE_URL}/repeat-purchase", json=payload, timeout=2.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    from app.schemas.ml import CustomerFeaturePayload
    service = get_cached_ml_service()
    resp = service.predict_repeat_purchase(CustomerFeaturePayload(**payload))
    return resp.model_dump()


def call_ai_ask_api(question: str) -> str:
    """Call POST /api/v1/ai/ask with fallback to cached AIService."""
    try:
        res = requests.post(f"{AI_API_BASE_URL}/ask", json={"question": question}, timeout=15.0)
        if res.status_code == 200:
            return res.json().get("answer", "")
    except Exception:
        pass

    return get_cached_ai_service().ask(question)


def call_ai_customer_report_api(customer_id: str) -> str:
    """Call POST /api/v1/ai/customer-report with fallback to cached AIService."""
    try:
        res = requests.post(f"{AI_API_BASE_URL}/customer-report", json={"customer_id": customer_id}, timeout=15.0)
        if res.status_code == 200:
            return res.json().get("report", "")
    except Exception:
        pass

    return get_cached_ai_service().get_customer_report(customer_id)


def call_ai_category_report_api(category: str) -> str:
    """Call POST /api/v1/ai/category-report with fallback to cached AIService."""
    try:
        res = requests.post(f"{AI_API_BASE_URL}/category-report", json={"category": category}, timeout=15.0)
        if res.status_code == 200:
            return res.json().get("report", "")
    except Exception:
        pass

    return get_cached_ai_service().get_category_report(category)


def call_ai_executive_summary_api() -> str:
    """Call GET /api/v1/ai/executive-summary with fallback to cached AIService."""
    try:
        res = requests.get(f"{AI_API_BASE_URL}/executive-summary", timeout=15.0)
        if res.status_code == 200:
            return res.json().get("summary", "")
    except Exception:
        pass

    return get_cached_ai_service().get_executive_summary()
