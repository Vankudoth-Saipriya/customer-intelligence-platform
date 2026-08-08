"""
Dashboard Data Provider.

Cached data provider layer for Streamlit pages consuming EDA JSON artifacts,
ML Parquet prediction tables, and FastAPI ML inference endpoints.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
import pandas as pd
import requests
import streamlit as st

from app.services.ml_service import MLService, get_ml_service

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
API_BASE_URL = "http://127.0.0.1:8000/api/v1/ml"


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
    return pd.read_parquet(path)


@st.cache_data
def get_customer_segments() -> pd.DataFrame:
    path = ARTIFACTS_DIR / "ml" / "customer_segments.parquet"
    return pd.read_parquet(path)


@st.cache_data
def get_clv_predictions() -> pd.DataFrame:
    path = ARTIFACTS_DIR / "ml" / "customer_clv_predictions.parquet"
    return pd.read_parquet(path)


@st.cache_data
def get_repeat_predictions() -> pd.DataFrame:
    path = ARTIFACTS_DIR / "ml" / "repeat_purchase_predictions.parquet"
    return pd.read_parquet(path)


def call_segment_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Call POST /api/v1/ml/segment with HTTP fallback to MLService.
    """
    payload = feature_payload or {"customer_id": customer_id}
    try:
        res = requests.post(f"{API_BASE_URL}/segment", json=payload, timeout=2.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    # Direct MLService fallback
    from app.schemas.ml import CustomerFeaturePayload
    service = get_ml_service()
    resp = service.predict_segment(CustomerFeaturePayload(**payload))
    return resp.model_dump()


def call_clv_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Call POST /api/v1/ml/clv with HTTP fallback to MLService.
    """
    payload = feature_payload or {"customer_id": customer_id}
    try:
        res = requests.post(f"{API_BASE_URL}/clv", json=payload, timeout=2.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    from app.schemas.ml import CustomerFeaturePayload
    service = get_ml_service()
    resp = service.predict_clv(CustomerFeaturePayload(**payload))
    return resp.model_dump()


def call_repeat_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Call POST /api/v1/ml/repeat-purchase with HTTP fallback to MLService.
    """
    payload = feature_payload or {"customer_id": customer_id}
    try:
        res = requests.post(f"{API_BASE_URL}/repeat-purchase", json=payload, timeout=2.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass

    from app.schemas.ml import CustomerFeaturePayload
    service = get_ml_service()
    resp = service.predict_repeat_purchase(CustomerFeaturePayload(**payload))
    return resp.model_dump()


AI_API_BASE_URL = "http://127.0.0.1:8000/api/v1/ai"


def call_ai_ask_api(question: str) -> str:
    """Call POST /api/v1/ai/ask with AIService fallback."""
    try:
        res = requests.post(f"{AI_API_BASE_URL}/ask", json={"question": question}, timeout=5.0)
        if res.status_code == 200:
            return res.json().get("answer", "")
    except Exception:
        pass

    from app.services.ai_service import get_ai_service
    return get_ai_service().ask(question)


def call_ai_customer_report_api(customer_id: str) -> str:
    """Call POST /api/v1/ai/customer-report with AIService fallback."""
    try:
        res = requests.post(f"{AI_API_BASE_URL}/customer-report", json={"customer_id": customer_id}, timeout=5.0)
        if res.status_code == 200:
            return res.json().get("report", "")
    except Exception:
        pass

    from app.services.ai_service import get_ai_service
    return get_ai_service().get_customer_report(customer_id)


def call_ai_category_report_api(category: str) -> str:
    """Call POST /api/v1/ai/category-report with AIService fallback."""
    try:
        res = requests.post(f"{AI_API_BASE_URL}/category-report", json={"category": category}, timeout=5.0)
        if res.status_code == 200:
            return res.json().get("report", "")
    except Exception:
        pass

    from app.services.ai_service import get_ai_service
    return get_ai_service().get_category_report(category)


def call_ai_executive_summary_api() -> str:
    """Call GET /api/v1/ai/executive-summary with AIService fallback."""
    try:
        res = requests.get(f"{AI_API_BASE_URL}/executive-summary", timeout=5.0)
        if res.status_code == 200:
            return res.json().get("summary", "")
    except Exception:
        pass

    from app.services.ai_service import get_ai_service
    return get_ai_service().get_executive_summary()

