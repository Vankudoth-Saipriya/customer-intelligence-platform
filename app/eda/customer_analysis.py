"""
Customer Exploratory Data Analysis (EDA) module.

Performs customer geographic distribution analysis, growth tracking over time,
repeat purchase rate evaluation, purchase distribution profiling, and spending overview.
"""

import time
from typing import Any, Dict, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data_loader import AnalyticsDataLoader
from app.analytics.data_profiler import DataProfiler
from app.eda.report import CustomerAnalysisReport


class CustomerAnalyzer:
    """
    Analyzer executing comprehensive Customer EDA and generating structured reports.
    """

    def __init__(
        self,
        data_loader: Optional[AnalyticsDataLoader] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Initialize CustomerAnalyzer with data loader or session.
        """
        self.data_loader = data_loader or AnalyticsDataLoader(session=session)
        self.profiler = DataProfiler()

    def analyze(self) -> CustomerAnalysisReport:
        """
        Execute full customer exploratory data analysis.

        Returns:
            CustomerAnalysisReport containing analytical statistics.
        """
        start_time = time.perf_counter()
        logger.info("Initiating Customer Exploratory Data Analysis (EDA)...")

        # Load domain datasets via AnalyticsDataLoader
        customers_df = self.data_loader.load_customers()
        orders_df = self.data_loader.load_orders()

        total_customers = len(customers_df)
        logger.info(f"Loaded {total_customers:,} customer records for EDA.")

        # Merge customers and orders for unique customer analysis
        merged_df = customers_df.merge(orders_df, on="customer_id", how="left")

        # ---------------------------------------------------------------------
        # 1. Customer Geographic Distribution
        # ---------------------------------------------------------------------
        logger.info("Analyzing customer geographic distribution...")
        state_counts = customers_df["customer_state"].value_counts().to_dict()
        city_counts_total = int(customers_df["customer_city"].nunique())
        top_20_cities = customers_df["customer_city"].value_counts().head(20).to_dict()

        geo_dist = {
            "state_distribution": state_counts,
            "total_cities_count": city_counts_total,
            "top_20_cities": top_20_cities,
        }

        # ---------------------------------------------------------------------
        # 2. Customer Growth Over Time
        # ---------------------------------------------------------------------
        logger.info("Analyzing customer growth over time...")
        merged_df["purchase_dt"] = pd.to_datetime(merged_df["order_purchase_timestamp"], errors="coerce", utc=True)
        first_purchases = merged_df.groupby("customer_unique_id")["purchase_dt"].min().reset_index()

        growth_by_year: Dict[str, int] = {}
        growth_by_month: Dict[str, int] = {}

        if not first_purchases["purchase_dt"].isnull().all():
            first_purchases["year"] = first_purchases["purchase_dt"].dt.year.fillna(0).astype(int).astype(str)
            first_purchases["year_month"] = first_purchases["purchase_dt"].dt.tz_localize(None).dt.to_period("M").astype(str)

            growth_by_year = first_purchases["year"].value_counts().sort_index().to_dict()
            growth_by_month = first_purchases["year_month"].value_counts().sort_index().to_dict()

        growth_over_time = {
            "customers_by_year": growth_by_year,
            "customers_by_month": growth_by_month,
        }

        # ---------------------------------------------------------------------
        # 3. Repeat Customer Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing repeat customer purchase rates...")
        unique_cust_count = int(customers_df["customer_unique_id"].nunique())
        orders_per_unique = merged_df.groupby("customer_unique_id")["order_id"].nunique()

        repeat_cust_count = int((orders_per_unique > 1).sum())
        repeat_rate = round((repeat_cust_count / unique_cust_count * 100.0), 2) if unique_cust_count > 0 else 0.0

        repeat_analysis = {
            "total_unique_customers": unique_cust_count,
            "repeat_customers": repeat_cust_count,
            "repeat_purchase_rate_percent": repeat_rate,
        }

        # ---------------------------------------------------------------------
        # 4. Customer Purchase Distribution
        # ---------------------------------------------------------------------
        logger.info("Analyzing purchase frequency distribution...")
        orders_hist_stats = {
            "mean_orders_per_customer": round(float(orders_per_unique.mean()), 2),
            "std_orders_per_customer": round(float(orders_per_unique.std()), 2) if len(orders_per_unique) > 1 else 0.0,
            "min_orders": int(orders_per_unique.min()) if len(orders_per_unique) > 0 else 0,
            "q25_orders": float(orders_per_unique.quantile(0.25)) if len(orders_per_unique) > 0 else 0.0,
            "median_orders": float(orders_per_unique.median()) if len(orders_per_unique) > 0 else 0.0,
            "q75_orders": float(orders_per_unique.quantile(0.75)) if len(orders_per_unique) > 0 else 0.0,
            "max_orders": int(orders_per_unique.max()) if len(orders_per_unique) > 0 else 0,
        }
        orders_per_cust_frequency = orders_per_unique.value_counts().sort_index().to_dict()

        purchase_distribution = {
            "orders_per_customer_histogram": orders_hist_stats,
            "order_frequency_counts": orders_per_cust_frequency,
        }

        # ---------------------------------------------------------------------
        # 5. Customer Spending Overview
        # ---------------------------------------------------------------------
        logger.info("Analyzing customer spending overview...")
        spent_per_cust = merged_df.groupby("customer_unique_id")["order_value"].sum().dropna()

        total_spent = round(float(spent_per_cust.sum()), 2)
        avg_spent = round(float(spent_per_cust.mean()), 2) if len(spent_per_cust) > 0 else 0.0
        min_spent = round(float(spent_per_cust.min()), 2) if len(spent_per_cust) > 0 else 0.0
        max_spent = round(float(spent_per_cust.max()), 2) if len(spent_per_cust) > 0 else 0.0

        q25_spent = round(float(spent_per_cust.quantile(0.25)), 2) if len(spent_per_cust) > 0 else 0.0
        q50_spent = round(float(spent_per_cust.median()), 2) if len(spent_per_cust) > 0 else 0.0
        q75_spent = round(float(spent_per_cust.quantile(0.75)), 2) if len(spent_per_cust) > 0 else 0.0

        spending_overview = {
            "total_spent_overall": total_spent,
            "average_spending_per_customer": avg_spent,
            "min_spending": min_spent,
            "max_spending": max_spent,
            "quartiles": {
                "q25": q25_spent,
                "q50_median": q50_spent,
                "q75": q75_spent,
            },
        }

        # ---------------------------------------------------------------------
        # 6. Customer Value Segmentation Tiers
        # ---------------------------------------------------------------------
        logger.info("Analyzing customer value segmentation tiers...")
        q25_val = spent_per_cust.quantile(0.25)
        q75_val = spent_per_cust.quantile(0.75)

        low_val_mask = spent_per_cust <= q25_val
        med_val_mask = (spent_per_cust > q25_val) & (spent_per_cust <= q75_val)
        high_val_mask = spent_per_cust > q75_val

        val_tiers = {
            "Low Value (Bottom 25%)": {
                "customer_count": int(low_val_mask.sum()),
                "revenue_contribution": round(float(spent_per_cust[low_val_mask].sum()), 2),
                "customer_percentage": round((low_val_mask.sum() / unique_cust_count * 100.0), 2) if unique_cust_count > 0 else 0.0,
                "revenue_percentage": round((spent_per_cust[low_val_mask].sum() / total_spent * 100.0), 2) if total_spent > 0 else 0.0,
            },
            "Medium Value (25%-75%)": {
                "customer_count": int(med_val_mask.sum()),
                "revenue_contribution": round(float(spent_per_cust[med_val_mask].sum()), 2),
                "customer_percentage": round((med_val_mask.sum() / unique_cust_count * 100.0), 2) if unique_cust_count > 0 else 0.0,
                "revenue_percentage": round((spent_per_cust[med_val_mask].sum() / total_spent * 100.0), 2) if total_spent > 0 else 0.0,
            },
            "High Value (Top 25%)": {
                "customer_count": int(high_val_mask.sum()),
                "revenue_contribution": round(float(spent_per_cust[high_val_mask].sum()), 2),
                "customer_percentage": round((high_val_mask.sum() / unique_cust_count * 100.0), 2) if unique_cust_count > 0 else 0.0,
                "revenue_percentage": round((spent_per_cust[high_val_mask].sum() / total_spent * 100.0), 2) if total_spent > 0 else 0.0,
            },
        }

        # ---------------------------------------------------------------------
        # 7. Customer Frequency Segmentation Tiers
        # ---------------------------------------------------------------------
        logger.info("Analyzing customer order frequency tiers...")
        one_time_mask = orders_per_unique == 1
        occasional_mask = (orders_per_unique >= 2) & (orders_per_unique <= 5)
        frequent_mask = orders_per_unique > 5

        # Align spending with order frequency series index
        aligned_spent = spent_per_cust.reindex(orders_per_unique.index).fillna(0.0)

        freq_tiers = {
            "One-time": {
                "customer_count": int(one_time_mask.sum()),
                "revenue_contribution": round(float(aligned_spent[one_time_mask].sum()), 2),
                "customer_percentage": round((one_time_mask.sum() / unique_cust_count * 100.0), 2) if unique_cust_count > 0 else 0.0,
                "revenue_percentage": round((aligned_spent[one_time_mask].sum() / total_spent * 100.0), 2) if total_spent > 0 else 0.0,
            },
            "Occasional (2-5 orders)": {
                "customer_count": int(occasional_mask.sum()),
                "revenue_contribution": round(float(aligned_spent[occasional_mask].sum()), 2),
                "customer_percentage": round((occasional_mask.sum() / unique_cust_count * 100.0), 2) if unique_cust_count > 0 else 0.0,
                "revenue_percentage": round((aligned_spent[occasional_mask].sum() / total_spent * 100.0), 2) if total_spent > 0 else 0.0,
            },
            "Frequent (>5 orders)": {
                "customer_count": int(frequent_mask.sum()),
                "revenue_contribution": round(float(aligned_spent[frequent_mask].sum()), 2),
                "customer_percentage": round((frequent_mask.sum() / unique_cust_count * 100.0), 2) if unique_cust_count > 0 else 0.0,
                "revenue_percentage": round((aligned_spent[frequent_mask].sum() / total_spent * 100.0), 2) if total_spent > 0 else 0.0,
            },
        }

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Customer EDA in {elapsed_sec:.4f}s.")

        report = CustomerAnalysisReport(
            total_customers_analyzed=total_customers,
            geographic_distribution=geo_dist,
            growth_over_time=growth_over_time,
            repeat_analysis=repeat_analysis,
            purchase_distribution=purchase_distribution,
            spending_overview=spending_overview,
            value_segmentation=val_tiers,
            frequency_segmentation=freq_tiers,
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save JSON artifact to artifacts/eda/customer_analysis.json
        report.save_json()

        return report
