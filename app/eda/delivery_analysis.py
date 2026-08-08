"""
Delivery Exploratory Data Analysis (EDA) module.

Performs delivery time distribution profiling, delivery delay evaluation,
regional state performance benchmarking, freight logistics correlation analysis,
and operational SLA achievement tracking.
"""

import time
from typing import Any, Dict, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data_loader import AnalyticsDataLoader
from app.analytics.data_profiler import DataProfiler
from app.eda.report import DeliveryAnalysisReport


class DeliveryAnalyzer:
    """
    Analyzer executing comprehensive Delivery EDA and generating structured reports.
    """

    def __init__(
        self,
        data_loader: Optional[AnalyticsDataLoader] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Initialize DeliveryAnalyzer with data loader or session.
        """
        self.data_loader = data_loader or AnalyticsDataLoader(session=session)
        self.profiler = DataProfiler()

    def analyze(self) -> DeliveryAnalysisReport:
        """
        Execute full delivery exploratory data analysis.

        Returns:
            DeliveryAnalysisReport containing analytical statistics.
        """
        start_time = time.perf_counter()
        logger.info("Initiating Delivery Exploratory Data Analysis (EDA)...")

        # Load domain datasets via AnalyticsDataLoader
        orders_df = self.data_loader.load_orders()
        customers_df = self.data_loader.load_customers()

        total_orders = len(orders_df)
        logger.info(f"Loaded {total_orders:,} order records for Delivery EDA.")

        # Ensure datetime parsing for timestamp columns
        p_dt = pd.to_datetime(orders_df["order_purchase_timestamp"], errors="coerce", utc=True)
        a_dt = pd.to_datetime(orders_df["order_approved_at"], errors="coerce", utc=True)
        c_dt = pd.to_datetime(orders_df["order_delivered_carrier_date"], errors="coerce", utc=True)
        d_dt = pd.to_datetime(orders_df["order_delivered_customer_date"], errors="coerce", utc=True)
        e_dt = pd.to_datetime(orders_df["order_estimated_delivery_date"], errors="coerce", utc=True)

        # Compute calculated time duration metrics (in days)
        orders_df["proc_days"] = (a_dt - p_dt).dt.total_seconds() / 86400.0
        orders_df["carrier_dispatch_days"] = (c_dt - a_dt).dt.total_seconds() / 86400.0
        orders_df["transit_days"] = (d_dt - c_dt).dt.total_seconds() / 86400.0
        orders_df["calc_delivery_days"] = (d_dt - p_dt).dt.total_seconds() / 86400.0
        orders_df["calc_delay_days"] = (d_dt - e_dt).dt.total_seconds() / 86400.0

        # Prefer pre-computed ORM columns if present, falling back to computed values
        if "delivery_days" not in orders_df.columns or orders_df["delivery_days"].isnull().all():
            orders_df["delivery_days"] = orders_df["calc_delivery_days"]
        if "delivery_delay_days" not in orders_df.columns or orders_df["delivery_delay_days"].isnull().all():
            orders_df["delivery_delay_days"] = orders_df["calc_delay_days"]

        # Delivered orders subset
        delivered_mask = orders_df["order_delivered_customer_date"].notnull()
        delivered_orders = orders_df[delivered_mask].copy()
        total_delivered = len(delivered_orders)
        logger.info(f"Analyzed {total_delivered:,} delivered order records.")

        # Merge delivered orders with customers to get state
        merged_orders = delivered_orders.merge(
            customers_df[["customer_id", "customer_state", "customer_city"]],
            on="customer_id",
            how="left",
        )

        # ---------------------------------------------------------------------
        # 1. Delivery Time Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing delivery times, medians, and distribution ranges...")

        del_series = delivered_orders["delivery_days"].dropna()

        avg_delivery_days = round(float(del_series.mean()), 2) if len(del_series) > 0 else 0.0
        median_delivery_days = round(float(del_series.median()), 2) if len(del_series) > 0 else 0.0
        min_delivery_days = round(float(del_series.min()), 2) if len(del_series) > 0 else 0.0
        max_delivery_days = round(float(del_series.max()), 2) if len(del_series) > 0 else 0.0

        q25_del = round(float(del_series.quantile(0.25)), 2) if len(del_series) > 0 else 0.0
        q50_del = median_delivery_days
        q75_del = round(float(del_series.quantile(0.75)), 2) if len(del_series) > 0 else 0.0

        # Binned delivery day distribution
        bins = [-np.inf, 3, 7, 14, 21, 30, np.inf]
        labels = ["0-3 days", "4-7 days", "8-14 days", "15-21 days", "22-30 days", ">30 days"]
        del_binned = pd.cut(del_series, bins=bins, labels=labels)
        del_dist_counts = del_binned.value_counts().sort_index()

        del_dist = {
            str(lbl): {
                "count": int(del_dist_counts[lbl]),
                "percentage": round((del_dist_counts[lbl] / total_delivered * 100.0), 2) if total_delivered > 0 else 0.0,
            }
            for lbl in labels
        }

        delivery_time_analysis = {
            "average_delivery_days": avg_delivery_days,
            "median_delivery_days": median_delivery_days,
            "min_delivery_days": min_delivery_days,
            "max_delivery_days": max_delivery_days,
            "delivery_time_quartiles": {
                "q25": q25_del,
                "q50_median": q50_del,
                "q75": q75_del,
            },
            "delivery_day_distribution": del_dist,
        }

        # ---------------------------------------------------------------------
        # 2. Delivery Delay Analysis
        # ---------------------------------------------------------------------
        logger.info("Evaluating delivery delays, late vs early deliveries, and SLA adherence...")

        delay_series = delivered_orders["delivery_delay_days"].dropna()

        avg_delay_days = round(float(delay_series.mean()), 2) if len(delay_series) > 0 else 0.0

        late_mask = delay_series > 0
        early_mask = delay_series < 0
        on_time_mask = delay_series <= 0

        late_count = int(late_mask.sum())
        early_count = int(early_mask.sum())
        on_time_count = int(on_time_mask.sum())

        late_pct = round((late_count / total_delivered * 100.0), 2) if total_delivered > 0 else 0.0
        early_pct = round((early_count / total_delivered * 100.0), 2) if total_delivered > 0 else 0.0
        on_time_pct = round((on_time_count / total_delivered * 100.0), 2) if total_delivered > 0 else 0.0

        avg_early_days = (
            round(float(abs(delay_series[early_mask].mean())), 2)
            if early_count > 0
            else 0.0
        )
        avg_late_days = (
            round(float(delay_series[late_mask].mean()), 2)
            if late_count > 0
            else 0.0
        )

        # Delay Binned Distribution
        delay_bins = [-np.inf, -10, 0, 5, 10, np.inf]
        delay_labels = [">10 days early", "0-10 days early", "1-5 days late", "6-10 days late", ">10 days late"]
        delay_binned = pd.cut(delay_series, bins=delay_bins, labels=delay_labels)
        delay_dist_counts = delay_binned.value_counts().sort_index()

        delay_dist = {
            str(lbl): {
                "count": int(delay_dist_counts[lbl]),
                "percentage": round((delay_dist_counts[lbl] / total_delivered * 100.0), 2) if total_delivered > 0 else 0.0,
            }
            for lbl in delay_labels
        }

        delivery_delay_analysis = {
            "average_delivery_delay_days": avg_delay_days,
            "percentage_of_late_deliveries": late_pct,
            "late_deliveries_summary": {
                "count": late_count,
                "percentage": late_pct,
                "average_days_late": avg_late_days,
            },
            "early_deliveries_summary": {
                "count": early_count,
                "percentage": early_pct,
                "average_days_early": avg_early_days,
            },
            "on_time_deliveries_summary": {
                "count": on_time_count,
                "percentage": on_time_pct,
            },
            "delay_distribution": delay_dist,
            "delay_statistics": {
                "mean": avg_delay_days,
                "std": round(float(delay_series.std()), 2) if len(delay_series) > 1 else 0.0,
                "min": round(float(delay_series.min()), 2) if len(delay_series) > 0 else 0.0,
                "q25": round(float(delay_series.quantile(0.25)), 2) if len(delay_series) > 0 else 0.0,
                "median": round(float(delay_series.median()), 2) if len(delay_series) > 0 else 0.0,
                "q75": round(float(delay_series.quantile(0.75)), 2) if len(delay_series) > 0 else 0.0,
                "max": round(float(delay_series.max()), 2) if len(delay_series) > 0 else 0.0,
                "skewness": round(float(delay_series.skew()), 4) if len(delay_series) > 2 else 0.0,
            },
        }

        # ---------------------------------------------------------------------
        # 3. Regional Delivery Performance
        # ---------------------------------------------------------------------
        logger.info("Analyzing regional delivery performance by state...")

        state_stats = merged_orders.groupby("customer_state").agg(
            avg_delivery_days=("delivery_days", "mean"),
            avg_delay_days=("delivery_delay_days", "mean"),
            late_rate=("is_late_delivery", "mean"),
            order_count=("order_id", "count"),
        ).reset_index()

        state_stats["avg_delivery_days"] = state_stats["avg_delivery_days"].round(2)
        state_stats["avg_delay_days"] = state_stats["avg_delay_days"].round(2)
        state_stats["late_rate"] = (state_stats["late_rate"] * 100.0).round(2)

        avg_del_by_state = (
            state_stats.set_index("customer_state")["avg_delivery_days"].to_dict()
        )
        avg_delay_by_state = (
            state_stats.set_index("customer_state")["avg_delay_days"].to_dict()
        )

        top_20_fastest = (
            state_stats.sort_values(by="avg_delivery_days", ascending=True)
            .head(20)
            .apply(
                lambda r: {
                    "state": str(r["customer_state"]),
                    "average_delivery_days": float(r["avg_delivery_days"]),
                    "average_delay_days": float(r["avg_delay_days"]),
                    "late_delivery_rate": float(r["late_rate"]),
                    "order_count": int(r["order_count"]),
                },
                axis=1,
            )
            .tolist()
        )

        top_20_slowest = (
            state_stats.sort_values(by="avg_delivery_days", ascending=False)
            .head(20)
            .apply(
                lambda r: {
                    "state": str(r["customer_state"]),
                    "average_delivery_days": float(r["avg_delivery_days"]),
                    "average_delay_days": float(r["avg_delay_days"]),
                    "late_delivery_rate": float(r["late_rate"]),
                    "order_count": int(r["order_count"]),
                },
                axis=1,
            )
            .tolist()
        )

        regional_delivery_performance = {
            "average_delivery_time_by_state": avg_del_by_state,
            "average_delivery_delay_by_state": avg_delay_by_state,
            "top_20_fastest_states": top_20_fastest,
            "top_20_slowest_states": top_20_slowest,
        }

        # ---------------------------------------------------------------------
        # 4. Freight & Logistics
        # ---------------------------------------------------------------------
        logger.info("Analyzing freight values, state distance proxies, and correlations...")

        valid_freight_del = merged_orders[["total_freight_value", "delivery_days"]].dropna()
        freight_vs_del_corr = (
            round(float(valid_freight_del["total_freight_value"].corr(valid_freight_del["delivery_days"])), 4)
            if len(valid_freight_del) > 1
            else 0.0
        )

        # Freight vs Distance Proxy (State average freight value)
        freight_by_state_series = (
            merged_orders.groupby("customer_state")["total_freight_value"]
            .mean()
            .round(2)
            .sort_values(ascending=False)
        )
        freight_vs_distance_proxy = freight_by_state_series.to_dict()

        # Freight Percentage of Order Value by State
        merged_orders["freight_pct"] = (
            merged_orders["total_freight_value"] / merged_orders["order_value"] * 100.0
        )
        freight_pct_by_state = (
            merged_orders.groupby("customer_state")["freight_pct"]
            .mean()
            .round(2)
            .sort_values(ascending=False)
            .to_dict()
        )

        # Freight Value Distribution
        fr_series = orders_df["total_freight_value"].dropna()
        freight_distribution = {
            "mean": round(float(fr_series.mean()), 2),
            "std": round(float(fr_series.std()), 2) if len(fr_series) > 1 else 0.0,
            "min": round(float(fr_series.min()), 2),
            "q25": round(float(fr_series.quantile(0.25)), 2),
            "median": round(float(fr_series.median()), 2),
            "q75": round(float(fr_series.quantile(0.75)), 2),
            "max": round(float(fr_series.max()), 2),
            "skewness": round(float(fr_series.skew()), 4) if len(fr_series) > 2 else 0.0,
        }

        freight_and_logistics = {
            "freight_vs_delivery_time_correlation": freight_vs_del_corr,
            "freight_vs_distance_proxy_state": freight_vs_distance_proxy,
            "freight_percentage_by_state": freight_pct_by_state,
            "freight_distribution": freight_distribution,
        }

        # ---------------------------------------------------------------------
        # 5. Operational Metrics
        # ---------------------------------------------------------------------
        logger.info("Computing operational timeline metrics and SLA achievement rates...")

        proc_series = orders_df["proc_days"].dropna()
        proc_series_clean = proc_series[proc_series >= 0]
        avg_processing_time = round(float(proc_series_clean.mean()), 2) if len(proc_series_clean) > 0 else 0.0

        carrier_series = orders_df["carrier_dispatch_days"].dropna()
        carrier_series_clean = carrier_series[carrier_series >= 0]
        avg_carrier_time = round(float(carrier_series_clean.mean()), 2) if len(carrier_series_clean) > 0 else 0.0

        transit_series = orders_df["transit_days"].dropna()
        transit_series_clean = transit_series[transit_series >= 0]
        avg_shipping_time = round(float(transit_series_clean.mean()), 2) if len(transit_series_clean) > 0 else 0.0

        sla_achievement_rate = on_time_pct

        operational_metrics = {
            "average_order_processing_time_days": avg_processing_time,
            "average_carrier_time_days": avg_carrier_time,
            "average_shipping_time_days": avg_shipping_time,
            "delivery_sla_achievement_rate_percent": sla_achievement_rate,
        }

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Delivery EDA in {elapsed_sec:.4f}s.")

        report = DeliveryAnalysisReport(
            total_orders_analyzed=total_orders,
            total_delivered_orders=total_delivered,
            delivery_time_analysis=delivery_time_analysis,
            delivery_delay_analysis=delivery_delay_analysis,
            regional_delivery_performance=regional_delivery_performance,
            freight_and_logistics=freight_and_logistics,
            operational_metrics=operational_metrics,
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save JSON artifact to artifacts/eda/delivery_analysis.json
        report.save_json()

        return report
