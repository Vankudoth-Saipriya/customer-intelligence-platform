"""
Review Exploratory Data Analysis (EDA) module.

Performs review score distribution analysis, comment text profiling,
customer satisfaction cross-tabulations, business correlation modeling,
and operational feedback metric computations.
"""

import time
from typing import Any, Dict, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data_loader import AnalyticsDataLoader
from app.analytics.data_profiler import DataProfiler
from app.eda.report import ReviewAnalysisReport


class ReviewAnalyzer:
    """
    Analyzer executing comprehensive Review EDA and generating structured reports.
    """

    def __init__(
        self,
        data_loader: Optional[AnalyticsDataLoader] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Initialize ReviewAnalyzer with data loader or session.
        """
        self.data_loader = data_loader or AnalyticsDataLoader(session=session)
        self.profiler = DataProfiler()

    def analyze(self) -> ReviewAnalysisReport:
        """
        Execute full review exploratory data analysis.

        Returns:
            ReviewAnalysisReport containing analytical statistics.
        """
        start_time = time.perf_counter()
        logger.info("Initiating Review Exploratory Data Analysis (EDA)...")

        # Load domain datasets via AnalyticsDataLoader
        reviews_df = self.data_loader.load_reviews()
        orders_df = self.data_loader.load_orders()
        customers_df = self.data_loader.load_customers()
        order_items_df = self.data_loader.load_order_items()
        products_df = self.data_loader.load_products()
        payments_df = self.data_loader.load_payments()

        total_reviews = len(reviews_df)
        logger.info(f"Loaded {total_reviews:,} review records for EDA.")

        # Ensure datetime parsing
        reviews_df["creation_dt"] = pd.to_datetime(reviews_df["review_creation_date"], errors="coerce", utc=True)
        reviews_df["year_month"] = reviews_df["creation_dt"].dt.tz_localize(None).dt.to_period("M").astype(str)

        # ---------------------------------------------------------------------
        # 1. Review Score Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing review score distributions, averages, and temporal trends...")

        scores_series = reviews_df["review_score"].dropna()
        score_dist_counts = scores_series.value_counts().sort_index()
        score_distribution = {str(int(k)): int(v) for k, v in score_dist_counts.items()}

        avg_score = round(float(scores_series.mean()), 2) if len(scores_series) > 0 else 0.0
        median_score = round(float(scores_series.median()), 2) if len(scores_series) > 0 else 0.0

        rating_percentages = {
            str(int(k)): round((v / total_reviews * 100.0), 2) if total_reviews > 0 else 0.0
            for k, v in score_dist_counts.items()
        }

        # Rating trend over time
        trend_df = (
            reviews_df.groupby("year_month")
            .agg(average_score=("review_score", "mean"), review_count=("review_id", "count"))
            .reset_index()
        )
        trend_df["average_score"] = trend_df["average_score"].round(2)
        rating_trend = {
            str(row["year_month"]): {
                "average_score": float(row["average_score"]),
                "review_count": int(row["review_count"]),
            }
            for _, row in trend_df.iterrows()
            if row["year_month"] != "NaT"
        }

        review_score_analysis = {
            "review_score_distribution": score_distribution,
            "average_review_score": avg_score,
            "median_review_score": median_score,
            "rating_percentages": rating_percentages,
            "rating_trend_over_time": rating_trend,
        }

        # ---------------------------------------------------------------------
        # 2. Review Text Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing review title/message presence and text lengths...")

        title_series = reviews_df["review_comment_title"].dropna().astype(str)
        msg_series = reviews_df["review_comment_message"].dropna().astype(str)

        title_count = len(title_series[title_series.str.strip() != ""])
        msg_count = len(msg_series[msg_series.str.strip() != ""])

        pct_title = round((title_count / total_reviews * 100.0), 2) if total_reviews > 0 else 0.0
        pct_msg = round((msg_count / total_reviews * 100.0), 2) if total_reviews > 0 else 0.0

        title_lens = title_series.apply(len)
        msg_lens = msg_series.apply(len)

        avg_msg_len = round(float(msg_lens.mean()), 2) if len(msg_lens) > 0 else 0.0

        def _calc_length_stats(lens: pd.Series) -> Dict[str, Any]:
            if len(lens) == 0:
                return {}
            return {
                "mean": round(float(lens.mean()), 2),
                "std": round(float(lens.std()), 2) if len(lens) > 1 else 0.0,
                "min": int(lens.min()),
                "q25": round(float(lens.quantile(0.25)), 2),
                "median": round(float(lens.median()), 2),
                "q75": round(float(lens.quantile(0.75)), 2),
                "max": int(lens.max()),
            }

        review_text_analysis = {
            "percentage_with_review_title": pct_title,
            "percentage_with_review_message": pct_msg,
            "average_review_message_length": avg_msg_len,
            "title_length_statistics": _calc_length_stats(title_lens),
            "message_length_statistics": _calc_length_stats(msg_lens),
        }

        # ---------------------------------------------------------------------
        # Merged Analytical Data Table for Satisfaction & Insights
        # ---------------------------------------------------------------------
        logger.info("Building joined analytical DataFrame for satisfaction and correlations...")

        # Calculate orders timestamps and delay/delivery days if needed
        p_dt = pd.to_datetime(orders_df["order_purchase_timestamp"], errors="coerce", utc=True)
        c_dt = pd.to_datetime(orders_df["order_delivered_carrier_date"], errors="coerce", utc=True)
        d_dt = pd.to_datetime(orders_df["order_delivered_customer_date"], errors="coerce", utc=True)
        e_dt = pd.to_datetime(orders_df["order_estimated_delivery_date"], errors="coerce", utc=True)

        if "delivery_days" not in orders_df.columns or orders_df["delivery_days"].isnull().all():
            orders_df["delivery_days"] = (d_dt - p_dt).dt.total_seconds() / 86400.0
        if "delivery_delay_days" not in orders_df.columns or orders_df["delivery_delay_days"].isnull().all():
            orders_df["delivery_delay_days"] = (d_dt - e_dt).dt.total_seconds() / 86400.0

        # Binned delivery time & delay buckets on orders_df
        del_bins = [-np.inf, 3, 7, 14, 21, 30, np.inf]
        del_labels = ["0-3 days", "4-7 days", "8-14 days", "15-21 days", "22-30 days", ">30 days"]
        orders_df["delivery_time_bucket"] = pd.cut(orders_df["delivery_days"], bins=del_bins, labels=del_labels).astype(str)

        delay_bins = [-np.inf, -10, 0, 5, 10, np.inf]
        delay_labels = [">10 days early", "0-10 days early", "1-5 days late", "6-10 days late", ">10 days late"]
        orders_df["delivery_delay_bucket"] = pd.cut(orders_df["delivery_delay_days"], bins=delay_bins, labels=delay_labels).astype(str)

        # Base merge: reviews -> orders -> customers
        merged_base = reviews_df.merge(
            orders_df[["order_id", "customer_id", "order_value", "delivery_days", "delivery_delay_days", "delivery_time_bucket", "delivery_delay_bucket", "is_delivered"]],
            on="order_id",
            how="left",
        ).merge(
            customers_df[["customer_id", "customer_state"]],
            on="customer_id",
            how="left",
        )

        # Merge for category: item -> product
        items_prod = order_items_df.merge(
            products_df[["product_id", "category_name_english", "product_category_name"]],
            on="product_id",
            how="left",
        )
        items_prod["effective_category"] = (
            items_prod["category_name_english"]
            .fillna(items_prod["product_category_name"])
            .fillna("Uncategorized")
        )
        order_cat_map = items_prod.groupby("order_id")["effective_category"].first().to_dict()

        # Merge for payment method: dominant payment method per order
        order_pmt_map = payments_df.groupby("order_id")["payment_type"].first().to_dict()

        merged_base["effective_category"] = merged_base["order_id"].map(order_cat_map).fillna("Uncategorized")
        merged_base["payment_type"] = merged_base["order_id"].map(order_pmt_map).fillna("Uncategorized")

        # ---------------------------------------------------------------------
        # 3. Customer Satisfaction Analysis
        # ---------------------------------------------------------------------
        logger.info("Computing customer satisfaction scores across categories, states, payments, and delivery buckets...")

        cat_satisfaction = (
            merged_base.groupby("effective_category")["review_score"]
            .agg(["mean", "count"])
            .rename(columns={"mean": "avg_score", "count": "review_count"})
            .round(2)
        )
        cat_sat_dict = cat_satisfaction["avg_score"].to_dict()

        state_satisfaction = (
            merged_base.groupby("customer_state")["review_score"]
            .mean()
            .round(2)
            .to_dict()
        )

        pmt_satisfaction = (
            merged_base.groupby("payment_type")["review_score"]
            .mean()
            .round(2)
            .to_dict()
        )

        delay_bucket_satisfaction = (
            merged_base[merged_base["delivery_delay_bucket"] != "nan"]
            .groupby("delivery_delay_bucket")["review_score"]
            .mean()
            .round(2)
            .to_dict()
        )

        time_bucket_satisfaction = (
            merged_base[merged_base["delivery_time_bucket"] != "nan"]
            .groupby("delivery_time_bucket")["review_score"]
            .mean()
            .round(2)
            .to_dict()
        )

        customer_satisfaction = {
            "average_review_score_by_product_category": cat_sat_dict,
            "average_review_score_by_state": state_satisfaction,
            "average_review_score_by_payment_method": pmt_satisfaction,
            "average_review_score_by_delivery_delay_bucket": delay_bucket_satisfaction,
            "average_review_score_by_delivery_time_bucket": time_bucket_satisfaction,
        }

        # ---------------------------------------------------------------------
        # 4. Business Insights
        # ---------------------------------------------------------------------
        logger.info("Calculating score correlations and top/bottom rated categories...")

        valid_delay = merged_base[["review_score", "delivery_delay_days"]].dropna()
        score_delay_corr = (
            round(float(valid_delay["review_score"].corr(valid_delay["delivery_delay_days"])), 4)
            if len(valid_delay) > 1
            else 0.0
        )

        valid_time = merged_base[["review_score", "delivery_days"]].dropna()
        score_time_corr = (
            round(float(valid_time["review_score"].corr(valid_time["delivery_days"])), 4)
            if len(valid_time) > 1
            else 0.0
        )

        valid_val = merged_base[["review_score", "order_value"]].dropna()
        score_val_corr = (
            round(float(valid_val["review_score"].corr(valid_val["order_value"])), 4)
            if len(valid_val) > 1
            else 0.0
        )

        # Categories with min 10 reviews
        filtered_cats = cat_satisfaction[cat_satisfaction["review_count"] >= 10]
        if len(filtered_cats) == 0:
            filtered_cats = cat_satisfaction

        highest_rated_cats = (
            filtered_cats.sort_values(by="avg_score", ascending=False)
            .head(10)
            .reset_index()
            .apply(lambda r: {"category": str(r["effective_category"]), "average_score": float(r["avg_score"]), "review_count": int(r["review_count"])}, axis=1)
            .tolist()
        )

        lowest_rated_cats = (
            filtered_cats.sort_values(by="avg_score", ascending=True)
            .head(10)
            .reset_index()
            .apply(lambda r: {"category": str(r["effective_category"]), "average_score": float(r["avg_score"]), "review_count": int(r["review_count"])}, axis=1)
            .tolist()
        )

        business_insights = {
            "review_score_vs_delivery_delay_correlation": score_delay_corr,
            "review_score_vs_delivery_time_correlation": score_time_corr,
            "review_score_vs_order_value_correlation": score_val_corr,
            "categories_with_highest_ratings": highest_rated_cats,
            "categories_with_lowest_ratings": lowest_rated_cats,
        }

        # ---------------------------------------------------------------------
        # 5. Operational Metrics
        # ---------------------------------------------------------------------
        logger.info("Computing operational sentiment metrics and review coverage...")

        pos_cnt = int((scores_series >= 4).sum())
        neu_cnt = int((scores_series == 3).sum())
        neg_cnt = int((scores_series <= 2).sum())

        pos_pct = round((pos_cnt / total_reviews * 100.0), 2) if total_reviews > 0 else 0.0

        # Review Coverage (% of delivered orders reviewed)
        delivered_orders_cnt = int((orders_df["order_delivered_customer_date"].notnull()).sum())
        reviewed_orders_cnt = int(reviews_df["order_id"].nunique())

        review_coverage_pct = (
            round((reviewed_orders_cnt / delivered_orders_cnt * 100.0), 2)
            if delivered_orders_cnt > 0
            else 0.0
        )

        operational_metrics = {
            "positive_reviews_count": pos_cnt,
            "neutral_reviews_count": neu_cnt,
            "negative_reviews_count": neg_cnt,
            "positive_review_percentage": pos_pct,
            "total_delivered_orders_count": delivered_orders_cnt,
            "reviewed_orders_count": reviewed_orders_cnt,
            "review_coverage_percentage": review_coverage_pct,
        }

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Review EDA in {elapsed_sec:.4f}s.")

        report = ReviewAnalysisReport(
            total_reviews_analyzed=total_reviews,
            review_score_analysis=review_score_analysis,
            review_text_analysis=review_text_analysis,
            customer_satisfaction=customer_satisfaction,
            business_insights=business_insights,
            operational_metrics=operational_metrics,
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save JSON artifact to artifacts/eda/review_analysis.json
        report.save_json()

        return report
