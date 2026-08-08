"""
Dashboard Data Provider Package.
"""

from app.dashboard.data_provider import (
    call_ai_ask_api,
    call_ai_category_report_api,
    call_ai_customer_report_api,
    call_ai_executive_summary_api,
    call_clv_api,
    call_repeat_api,
    call_segment_api,
    get_clv_predictions,
    get_customer_eda,
    get_customer_segments,
    get_delivery_eda,
    get_feature_store,
    get_payment_eda,
    get_product_eda,
    get_repeat_predictions,
    get_review_eda,
    get_sales_eda,
)

__all__ = [
    "get_customer_eda",
    "get_product_eda",
    "get_sales_eda",
    "get_delivery_eda",
    "get_payment_eda",
    "get_review_eda",
    "get_feature_store",
    "get_customer_segments",
    "get_clv_predictions",
    "get_repeat_predictions",
    "call_segment_api",
    "call_clv_api",
    "call_repeat_api",
    "call_ai_ask_api",
    "call_ai_customer_report_api",
    "call_ai_category_report_api",
    "call_ai_executive_summary_api",
]
