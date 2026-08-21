"""
Shared Artifact Data Store — Memory-Optimized.

Provides a single process-level cached layer for all Parquet prediction tables.
Every subsystem (ml_service, data_provider) imports from here instead of calling
pd.read_parquet independently.

Design goals:
- Each table is loaded exactly ONCE per process.
- Only the columns required across ALL consumers are read from disk.
- Column lists are hardcoded from verified pyarrow schema inspection.
- Categorical string columns are stored as pd.CategoricalDtype to reduce RAM.
- Module-level singletons — no copies, no Streamlit cache overhead.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# ---------------------------------------------------------------------------
# Hardcoded column projections — verified against actual parquet schemas.
# Only columns consumed by any dashboard page or service function.
# ---------------------------------------------------------------------------
_SEG_COLS: List[str] = [
    "customer_id", "customer_unique_id",
    "cluster_id", "cluster_description",
    "total_revenue", "frequency_orders", "avg_review_score",
]

_CLV_COLS: List[str] = [
    "customer_id", "customer_unique_id",
    "total_revenue", "target_future_clv", "predicted_clv",
    "customer_value_tier", "state", "frequency_orders",
]

_RP_COLS: List[str] = [
    "customer_id", "customer_unique_id",
    "target_repeat_buyer", "repeat_customer", "repeat_propensity_score", "repeat_propensity", "predicted_repeat_buyer", "predicted_repeat_customer",
]

_FS_COLS: List[str] = [
    "customer_id", "customer_unique_id",
    "customer_age_days", "frequency_orders", "monetary_value",
    "recency_days", "customer_value_tier", "state",
    "total_revenue", "avg_order_value", "avg_review_score",
    "favorite_product_category", "city",
]

# ---------------------------------------------------------------------------
# Dtype optimizations
# ---------------------------------------------------------------------------
_SEG_DTYPES: Dict[str, str] = {
    "cluster_description": "category",
}
_CLV_DTYPES: Dict[str, str] = {
    "customer_value_tier": "category",
    "state": "category",
}
_RP_DTYPES: Dict[str, str] = {
    "repeat_customer": "int8",
    "predicted_repeat_customer": "int8",
}
_FS_DTYPES: Dict[str, str] = {
    "customer_value_tier": "category",
    "state": "category",
    "favorite_product_category": "category",
    "city": "category",
}

# ---------------------------------------------------------------------------
# Process-level singletons — loaded once, never copied.
# ---------------------------------------------------------------------------
_seg_df: Optional[pd.DataFrame] = None
_clv_df: Optional[pd.DataFrame] = None
_rp_df: Optional[pd.DataFrame] = None
_fs_df: Optional[pd.DataFrame] = None


def _load(path: Path, cols: List[str], dtypes: Dict[str, str]) -> Optional[pd.DataFrame]:
    """
    Load a parquet file selecting only `cols` in a SINGLE read pass.
    Then downcast with `dtypes` to minimise in-process RAM.
    Returns None if the file is missing.
    """
    if not path.exists():
        return None

    try:
        import pyarrow.parquet as pq
        available = set(pq.read_schema(path).names)
        safe_cols = [c for c in cols if c in available]
    except Exception:
        safe_cols = cols

    df = pd.read_parquet(path, columns=safe_cols if safe_cols else None)

    try:
        import gc
        import pyarrow as pa
        pa.default_memory_pool().release_unused()
        gc.collect()
    except Exception:
        pass

    for col, dtype in dtypes.items():
        if col in df.columns:
            try:
                df[col] = df[col].astype(dtype)
            except Exception:
                pass

    return df


def get_segments() -> Optional[pd.DataFrame]:
    """Return cached customer_segments DataFrame (loaded once)."""
    global _seg_df
    if _seg_df is None:
        _seg_df = _load(
            ARTIFACTS_DIR / "ml" / "customer_segments.parquet",
            _SEG_COLS, _SEG_DTYPES,
        )
    return _seg_df


def get_clv_predictions() -> Optional[pd.DataFrame]:
    """Return cached customer_clv_predictions DataFrame (loaded once)."""
    global _clv_df
    if _clv_df is None:
        _clv_df = _load(
            ARTIFACTS_DIR / "ml" / "customer_clv_predictions.parquet",
            _CLV_COLS, _CLV_DTYPES,
        )
    return _clv_df


def get_repeat_predictions() -> Optional[pd.DataFrame]:
    """Return cached repeat_purchase_predictions DataFrame (loaded once)."""
    global _rp_df
    if _rp_df is None:
        _rp_df = _load(
            ARTIFACTS_DIR / "ml" / "repeat_purchase_predictions.parquet",
            _RP_COLS, _RP_DTYPES,
        )
    return _rp_df


def get_feature_store() -> Optional[pd.DataFrame]:
    """Return cached customer_feature_store DataFrame (loaded once)."""
    global _fs_df
    if _fs_df is None:
        _fs_df = _load(
            ARTIFACTS_DIR / "features" / "customer_feature_store.parquet",
            _FS_COLS, _FS_DTYPES,
        )
    return _fs_df
