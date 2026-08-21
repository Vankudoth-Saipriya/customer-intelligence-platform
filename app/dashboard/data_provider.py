"""
Dashboard Data Provider.

Cached data provider layer for Streamlit pages consuming EDA JSON artifacts,
ML Parquet prediction tables, and FastAPI ML inference endpoints.

Memory optimization:
- EDA JSON functions use @st.cache_data(ttl=3600, max_entries=1) so Streamlit
  keeps at most one copy and evicts after 1 hour.
- Parquet DataFrame getters do NOT use @st.cache_data — they delegate directly
  to artifact_store singletons. @st.cache_data would copy 122 MB of DataFrames
  into Streamlit's internal store on every page navigation rerun, accumulating
  hundreds of MB and triggering Exit 137. The singletons are already cached at
  the module level; no copy is needed.
"""

import gc
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from typing import Any, Dict, Optional
import pandas as pd
import requests
import streamlit as st

from app.analytics import artifact_store
from app.services.ml_service import MLService, get_ml_service

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
API_HOST = os.getenv("API_URL", "").rstrip("/")
if not API_HOST:
    if os.getenv("ENVIRONMENT") == "production":
        API_HOST = "https://customer-intelligence-api.onrender.com"
    else:
        API_HOST = "http://127.0.0.1:8000"

API_BASE_URL = f"{API_HOST}/api/v1/ml"


@st.cache_resource
def get_cached_ml_service() -> MLService:
    """Cache singleton MLService resource in memory."""
    return get_ml_service()


# ---------------------------------------------------------------------------
# EDA JSON loaders — use @st.cache_data with TTL + max_entries=1
# so Streamlit keeps exactly one copy per function and evicts stale ones.
# JSON files are small (<1 MB each) so caching them is fine.
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, max_entries=1)
def get_customer_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "customer_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600, max_entries=1)
def get_product_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "product_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600, max_entries=1)
def get_sales_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "sales_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600, max_entries=1)
def get_delivery_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "delivery_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600, max_entries=1)
def get_payment_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "payment_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600, max_entries=1)
def get_review_eda() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "eda" / "review_analysis.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=3600, max_entries=1)
def get_clv_metadata() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "ml" / "customer_clv_metadata.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=3600, max_entries=1)
def get_repeat_metadata() -> Dict[str, Any]:
    path = ARTIFACTS_DIR / "ml" / "repeat_purchase_metadata.json"
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data(ttl=3600, max_entries=1)
def get_cohort_retention_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    from app.analytics.advanced_analytics import CohortRetentionAnalyzer
    analyzer = CohortRetentionAnalyzer()
    return analyzer.compute_retention_matrix()


@st.cache_data(ttl=3600, max_entries=1)
def get_pareto_data() -> Dict[str, Any]:
    from app.analytics.advanced_analytics import ParetoRevenueAnalyzer
    analyzer = ParetoRevenueAnalyzer()
    return analyzer.analyze_concentration()


@st.cache_data(ttl=3600, max_entries=1)
def get_statistical_tests_data() -> Dict[str, Any]:
    from app.analytics.advanced_analytics import InferentialStatisticalTester
    tester = InferentialStatisticalTester()
    return {
        "delivery_vs_satisfaction": tester.test_delivery_delay_vs_satisfaction(),
        "repeat_vs_single_spend": tester.test_repeat_buyer_spend_difference(),
        "state_delivery_delay_anova": tester.test_state_delivery_delay_anova(),
    }


@st.cache_data(ttl=3600, max_entries=1)
def get_seller_performance_data() -> pd.DataFrame:
    from app.analytics.advanced_analytics import SellerPerformanceAnalyzer
    analyzer = SellerPerformanceAnalyzer()
    return analyzer.analyze_sellers()


@st.cache_data(ttl=3600, max_entries=1)
def get_data_quality_audit() -> Dict[str, Any]:
    from app.analytics.data_loader import AnalyticsDataLoader
    from app.analytics.data_profiler import DataProfiler
    loader = AnalyticsDataLoader()
    orders = loader.load_orders()
    payments = loader.load_payments()
    return DataProfiler.audit_order_status_and_revenue(orders, payments)


@st.cache_data(ttl=3600, max_entries=1)
def get_executive_kpis() -> Dict[str, Any]:
    sales_eda = get_sales_eda() or {}
    cust_eda = get_customer_eda() or {}
    return {
        "total_orders": sales_eda.get("total_orders_analyzed", 99441),
        "total_customers": cust_eda.get("total_customers_analyzed", 96096),
        "average_order_value": sales_eda.get("order_analysis", {}).get("average_order_value", 160.99),
        "total_revenue": sales_eda.get("revenue_analysis", {}).get("total_revenue", 16008872.12),
    }


@st.cache_data(ttl=3600, max_entries=1)
def get_monthly_revenue_data() -> pd.DataFrame:
    sales_eda = get_sales_eda() or {}
    monthly_list = sales_eda.get("monthly_revenue", [])
    if monthly_list:
        df_m = pd.DataFrame(monthly_list)
        if "total_revenue" in df_m.columns and "net_revenue" not in df_m.columns:
            df_m["net_revenue"] = df_m["total_revenue"]
        if "net_revenue" in df_m.columns and "cumulative_revenue" not in df_m.columns:
            df_m["cumulative_revenue"] = df_m["net_revenue"].cumsum()
        return df_m
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# Parquet DataFrame getters — direct passthrough to artifact_store singletons.
# NO @st.cache_data here: that would copy 30-45 MB DataFrames into Streamlit's
# internal cache store on every page rerun, accumulating RAM until OOM kill.
# The artifact_store module-level globals are already the canonical single copy.
# ---------------------------------------------------------------------------

def get_feature_store() -> pd.DataFrame:
    df = artifact_store.get_feature_store()
    if df is None:
        raise FileNotFoundError("customer_feature_store.parquet not found")
    return df


def get_customer_segments() -> pd.DataFrame:
    df = artifact_store.get_segments()
    if df is None:
        raise FileNotFoundError("customer_segments.parquet not found")
    return df


def get_clv_predictions() -> pd.DataFrame:
    df = artifact_store.get_clv_predictions()
    if df is None:
        raise FileNotFoundError("customer_clv_predictions.parquet not found")
    return df


def get_repeat_predictions() -> pd.DataFrame:
    df = artifact_store.get_repeat_predictions()
    if df is None:
        raise FileNotFoundError("repeat_purchase_predictions.parquet not found")
    return df


def get_customer_segmentation_data() -> pd.DataFrame:
    """Alias for get_customer_segments()."""
    return get_customer_segments()


def get_clv_prediction_data() -> pd.DataFrame:
    """Alias for get_clv_predictions()."""
    return get_clv_predictions()


def get_delivery_kpis() -> Dict[str, Any]:
    """Helper aggregating delivery EDA KPIs for Logistics page."""
    delivery_eda = get_delivery_eda() or {}
    op_metrics = delivery_eda.get("operational_metrics", {})
    rev_deliv = delivery_eda.get("review_impact_analysis", {})
    state_perf = delivery_eda.get("state_performance", {})
    return {
        "average_delivery_days": op_metrics.get("average_delivery_duration_days", 12.5),
        "late_delivery_rate_pct": op_metrics.get("late_delivery_rate_percent", 7.8),
        "on_time_avg_score": rev_deliv.get("ontime_avg_review_score", 4.29),
        "late_avg_score": rev_deliv.get("late_avg_review_score", 2.57),
        "fastest_states": state_perf.get("top_fastest_states", []),
        "slowest_states": state_perf.get("top_slowest_states", []),
    }


# ---------------------------------------------------------------------------
# Direct backend service callers (no unnecessary HTTP roundtrips)
# ---------------------------------------------------------------------------

def call_segment_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Direct in-process call to MLService for customer segment inference."""
    payload = feature_payload or {"customer_id": customer_id}
    from app.schemas.ml import CustomerFeaturePayload
    service = get_cached_ml_service()
    resp = service.predict_segment(CustomerFeaturePayload(**payload))
    return resp.model_dump()


def call_clv_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Direct in-process call to MLService for CLV prediction."""
    payload = feature_payload or {"customer_id": customer_id}
    from app.schemas.ml import CustomerFeaturePayload
    service = get_cached_ml_service()
    resp = service.predict_clv(CustomerFeaturePayload(**payload))
    return resp.model_dump()


def call_repeat_api(customer_id: str, feature_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Direct in-process call to MLService for repeat purchase propensity."""
    payload = feature_payload or {"customer_id": customer_id}
    from app.schemas.ml import CustomerFeaturePayload
    service = get_cached_ml_service()
    resp = service.predict_repeat_purchase(CustomerFeaturePayload(**payload))
    return resp.model_dump()



