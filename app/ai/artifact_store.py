"""
Shared Artifact Data Store.

Provides a single process-level cached layer for all Parquet prediction tables.
Every subsystem (ml_service, ai/tools, ai/analyst) imports from here instead of
calling pd.read_parquet independently.

Design goals:
- Each table is loaded exactly once per process.
- Only the columns required across ALL consumers are loaded (column projection).
- Module-level singletons mean Streamlit's @st.cache_resource is not required here;
  the objects live for the lifetime of the Python process.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"

# ---------------------------------------------------------------------------
# Column projections — only what any consumer actually reads
# ---------------------------------------------------------------------------
_SEG_COLS = [
    "customer_id", "customer_unique_id",
    "cluster_id", "cluster_name", "cluster_description",
    "total_revenue", "frequency_orders", "avg_review_score",
]

_CLV_COLS = [
    "customer_id", "customer_unique_id",
    "total_revenue", "predicted_clv",
    "customer_value_tier", "state", "frequency_orders",
]

_RP_COLS = [
    "customer_id", "customer_unique_id",
    "repeat_customer", "repeat_propensity", "predicted_repeat_customer",
]

_FS_COLS = [
    "customer_id", "customer_unique_id",
    "customer_age_days", "frequency_orders", "monetary_value",
    "recency_days", "customer_value_tier", "state",
    "total_revenue", "avg_order_value", "avg_review_score",
    "favorite_product_category", "city",
]

# ---------------------------------------------------------------------------
# Process-level singletons
# ---------------------------------------------------------------------------
_seg_df: Optional[pd.DataFrame] = None
_clv_df: Optional[pd.DataFrame] = None
_rp_df: Optional[pd.DataFrame] = None
_fs_df: Optional[pd.DataFrame] = None


def _load(path: Path, cols: list[str]) -> Optional[pd.DataFrame]:
    """Load a parquet file with column projection; return None if missing."""
    if not path.exists():
        return None
    available = set(pd.read_parquet(path, columns=None).columns)  # schema peek
    # Filter to only columns that exist (defensive)
    safe_cols = [c for c in cols if c in available]
    return pd.read_parquet(path, columns=safe_cols)


def get_segments() -> Optional[pd.DataFrame]:
    """Return cached customer_segments DataFrame (loaded once)."""
    global _seg_df
    if _seg_df is None:
        _seg_df = _load(ARTIFACTS_DIR / "ml" / "customer_segments.parquet", _SEG_COLS)
    return _seg_df


def get_clv_predictions() -> Optional[pd.DataFrame]:
    """Return cached customer_clv_predictions DataFrame (loaded once)."""
    global _clv_df
    if _clv_df is None:
        _clv_df = _load(ARTIFACTS_DIR / "ml" / "customer_clv_predictions.parquet", _CLV_COLS)
    return _clv_df


def get_repeat_predictions() -> Optional[pd.DataFrame]:
    """Return cached repeat_purchase_predictions DataFrame (loaded once)."""
    global _rp_df
    if _rp_df is None:
        _rp_df = _load(ARTIFACTS_DIR / "ml" / "repeat_purchase_predictions.parquet", _RP_COLS)
    return _rp_df


def get_feature_store() -> Optional[pd.DataFrame]:
    """Return cached customer_feature_store DataFrame (loaded once)."""
    global _fs_df
    if _fs_df is None:
        _fs_df = _load(ARTIFACTS_DIR / "features" / "customer_feature_store.parquet", _FS_COLS)
    return _fs_df
