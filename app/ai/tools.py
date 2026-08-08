"""
AI Business Analyst Modular Tools.

Provides structured JSON metrics and data extractions from existing EDA artifacts,
Customer Feature Store, and ML model predictions.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.ai import artifact_store

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"


class BaseTool:
    """Base class for AI Analyst Tools."""

    def run(self) -> Dict[str, Any]:
        raise NotImplementedError


class RevenueTool(BaseTool):
    """Tool extracting revenue, sales trajectory, and AOV metrics."""

    def run(self) -> Dict[str, Any]:
        sales_path = ARTIFACTS_DIR / "eda" / "sales_analysis.json"
        if not sales_path.exists():
            return {"error": "sales_analysis.json not found"}
        with open(sales_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "total_revenue": data.get("revenue_analysis", {}).get("total_revenue"),
            "revenue_by_year": data.get("revenue_analysis", {}).get("revenue_by_year"),
            "total_orders": data.get("order_analysis", {}).get("total_orders"),
            "average_order_value": data.get("order_analysis", {}).get("average_order_value"),
            "highest_revenue_months": data.get("sales_performance", {}).get("highest_revenue_months", [])[:5],
            "lowest_revenue_months": data.get("sales_performance", {}).get("lowest_revenue_months", [])[:5],
            "revenue_concentration": data.get("sales_performance", {}).get("revenue_concentration", {}),
        }


class CustomerTool(BaseTool):
    """Tool extracting customer demographic, growth, and RFM metrics."""

    def run(self) -> Dict[str, Any]:
        cust_path = ARTIFACTS_DIR / "eda" / "customer_analysis.json"
        if not cust_path.exists():
            return {"error": "customer_analysis.json not found"}
        with open(cust_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "total_customers": data.get("total_customers_analyzed"),
            "top_5_states": dict(list(data.get("geographic_distribution", {}).get("top_20_states", {}).items())[:5]),
            "rfm_summary": data.get("rfm_analysis", {}),
            "customer_growth_latest": list(data.get("customer_growth", {}).get("monthly_new_customers", {}).items())[-6:],
        }


class ProductTool(BaseTool):
    """Tool extracting product category revenue, performance, and freight correlations."""

    def run(self) -> Dict[str, Any]:
        prod_path = ARTIFACTS_DIR / "eda" / "product_analysis.json"
        if not prod_path.exists():
            return {"error": "product_analysis.json not found"}
        with open(prod_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        top_cats = dict(list(data.get("product_category_analysis", {}).get("revenue_by_category", {}).items())[:10])

        return {
            "total_products_analyzed": data.get("total_products_analyzed"),
            "top_10_revenue_categories": top_cats,
            "products_with_sales": data.get("product_performance", {}).get("total_products_with_sales"),
            "freight_vs_weight_corr": data.get("freight_analysis", {}).get("freight_vs_weight_correlation"),
            "translation_coverage_pct": data.get("translation_coverage", {}).get("translation_coverage_percentage"),
        }


class DeliveryTool(BaseTool):
    """Tool extracting delivery duration, delays, and SLA achievement metrics."""

    def run(self) -> Dict[str, Any]:
        deliv_path = ARTIFACTS_DIR / "eda" / "delivery_analysis.json"
        if not deliv_path.exists():
            return {"error": "delivery_analysis.json not found"}
        with open(deliv_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "average_delivery_days": data.get("delivery_time_analysis", {}).get("average_delivery_days"),
            "average_delivery_delay": data.get("delivery_delay_analysis", {}).get("average_delivery_delay"),
            "percentage_late_deliveries": data.get("delivery_delay_analysis", {}).get("percentage_late_deliveries"),
            "delivery_sla_achievement_rate": data.get("operational_metrics", {}).get("delivery_sla_achievement_rate"),
            "fastest_states": [s.get("state") for s in data.get("regional_delivery_performance", {}).get("top_20_fastest_states", [])[:5]],
            "slowest_states": [s.get("state") for s in data.get("regional_delivery_performance", {}).get("top_20_slowest_states", [])[:5]],
        }


class PaymentTool(BaseTool):
    """Tool extracting payment method shares, installments, and payment values."""

    def run(self) -> Dict[str, Any]:
        pay_path = ARTIFACTS_DIR / "eda" / "payment_analysis.json"
        if not pay_path.exists():
            return {"error": "payment_analysis.json not found"}
        with open(pay_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "total_payment_value": data.get("payment_value_analysis", {}).get("total_payment_value"),
            "average_payment_value": data.get("payment_value_analysis", {}).get("average_payment_value"),
            "payment_method_contributions_pct": data.get("business_metrics", {}).get("payment_method_contribution_pct"),
            "average_installment_count": data.get("installment_analysis", {}).get("average_installment_count"),
            "installment_revenue_contribution_pct": data.get("business_metrics", {}).get("installment_revenue_contribution_pct"),
        }


class ReviewTool(BaseTool):
    """Tool extracting review score distributions, sentiment, and SLA correlation."""

    def run(self) -> Dict[str, Any]:
        rev_path = ARTIFACTS_DIR / "eda" / "review_analysis.json"
        if not rev_path.exists():
            return {"error": "review_analysis.json not found"}
        with open(rev_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "total_reviews_analyzed": data.get("total_reviews_analyzed"),
            "average_review_score": data.get("review_score_analysis", {}).get("average_review_score"),
            "review_score_distribution": data.get("review_score_analysis", {}).get("review_score_distribution"),
            "positive_review_percentage": data.get("operational_metrics", {}).get("positive_review_percentage"),
            "review_score_vs_delivery_delay_correlation": data.get("business_insights", {}).get("review_score_vs_delivery_delay_correlation"),
        }


class SegmentationTool(BaseTool):
    """Tool extracting customer segmentation ML cluster profiles and statistics."""

    def run(self) -> Dict[str, Any]:
        meta_path = ARTIFACTS_DIR / "ml" / "customer_segmentation_metadata.json"

        df_seg = artifact_store.get_segments()
        if df_seg is None:
            return {"error": "customer_segments.parquet not found"}

        meta = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

        clusters = {}
        for cid, group in df_seg.groupby("cluster_id"):
            c_name = group["cluster_name"].iloc[0] if "cluster_name" in group.columns else f"Cluster {cid}"
            c_desc = group["cluster_description"].iloc[0] if "cluster_description" in group.columns else f"Cluster {cid} Profile"
            clusters[f"cluster_{cid}"] = {
                "cluster_name": c_name,
                "business_description": c_desc,
                "customer_count": int(len(group)),
                "customer_percentage": float(len(group) / len(df_seg) * 100),
                "avg_revenue": float(group["total_revenue"].mean()),
                "avg_orders": float(group["frequency_orders"].mean()),
                "avg_review_score": float(group["avg_review_score"].mean()),
            }

        return {
            "best_k": meta.get("best_k", 2),
            "best_silhouette_score": meta.get("best_silhouette_score"),
            "total_customers": len(df_seg),
            "cluster_profiles": clusters,
        }


class CLVTool(BaseTool):
    """Tool extracting CLV regressor performance metrics and top customer predictions."""

    def run(self) -> Dict[str, Any]:
        meta_path = ARTIFACTS_DIR / "ml" / "customer_clv_metadata.json"

        df_clv = artifact_store.get_clv_predictions()
        if df_clv is None:
            return {"error": "customer_clv_predictions.parquet not found"}

        meta = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

        top_10 = df_clv.sort_values(by="predicted_clv", ascending=False).head(10)[
            ["customer_id", "total_revenue", "predicted_clv"]
        ].to_dict(orient="records")

        return {
            "selected_model": meta.get("best_model_name", "Random Forest Regressor"),
            "metrics": meta.get("model_metrics", {}).get(meta.get("best_model_name"), {}),
            "mean_predicted_clv": float(df_clv["predicted_clv"].mean()),
            "median_predicted_clv": float(df_clv["predicted_clv"].median()),
            "max_predicted_clv": float(df_clv["predicted_clv"].max()),
            "top_10_predicted_customers": top_10,
        }


class RepeatPurchaseTool(BaseTool):
    """Tool extracting repeat purchase propensity classifier metrics and summary."""

    def run(self) -> Dict[str, Any]:
        meta_path = ARTIFACTS_DIR / "ml" / "repeat_purchase_metadata.json"

        df_rp = artifact_store.get_repeat_predictions()
        if df_rp is None:
            return {"error": "repeat_purchase_predictions.parquet not found"}

        meta = {}
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)

        return {
            "selected_model": meta.get("best_model_name", "Logistic Regression"),
            "metrics": meta.get("model_metrics", {}).get(meta.get("best_model_name"), {}),
            "total_customers": len(df_rp),
            "predicted_repeat_buyers": int((df_rp["predicted_repeat_customer"] == 1).sum()),
            "repeat_buyer_percentage": float((df_rp["predicted_repeat_customer"] == 1).mean() * 100),
            "mean_repeat_propensity": float(df_rp["repeat_propensity"].mean()),
        }
