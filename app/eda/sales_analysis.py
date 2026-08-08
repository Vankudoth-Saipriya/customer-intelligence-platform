"""
Sales Exploratory Data Analysis (EDA) module.

Performs revenue analysis, order frequency & temporal distribution profiling,
seasonality tracking, holiday spike detection, sales performance evaluation,
and operational unit metrics computation.
"""

import time
from typing import Any, Dict, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data_loader import AnalyticsDataLoader
from app.analytics.data_profiler import DataProfiler
from app.eda.report import SalesAnalysisReport


class SalesAnalyzer:
    """
    Analyzer executing comprehensive Sales EDA and generating structured reports.
    """

    def __init__(
        self,
        data_loader: Optional[AnalyticsDataLoader] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Initialize SalesAnalyzer with data loader or session.
        """
        self.data_loader = data_loader or AnalyticsDataLoader(session=session)
        self.profiler = DataProfiler()

    def analyze(self) -> SalesAnalysisReport:
        """
        Execute full sales exploratory data analysis.

        Returns:
            SalesAnalysisReport containing analytical statistics.
        """
        start_time = time.perf_counter()
        logger.info("Initiating Sales Exploratory Data Analysis (EDA)...")

        # Load datasets via AnalyticsDataLoader
        orders_df = self.data_loader.load_orders()
        order_items_df = self.data_loader.load_order_items()
        customers_df = self.data_loader.load_customers()
        products_df = self.data_loader.load_products()

        total_orders = len(orders_df)
        logger.info(f"Loaded {total_orders:,} order records for Sales EDA.")

        # Ensure datetime parsing for order purchase timestamps
        orders_df["purchase_dt"] = pd.to_datetime(
            orders_df["order_purchase_timestamp"], errors="coerce", utc=True
        )
        orders_df["purchase_dt_naive"] = orders_df["purchase_dt"].dt.tz_localize(None)

        # ---------------------------------------------------------------------
        # 1. Revenue Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing revenue breakdown, temporal aggregates, and growth rates...")

        total_items_revenue = round(float(orders_df["total_items_price"].sum()), 2)
        total_freight_revenue = round(float(orders_df["total_freight_value"].sum()), 2)
        total_overall_revenue = round(float(orders_df["order_value"].sum()), 2)

        # Revenue by Year
        orders_df["year"] = orders_df["purchase_dt_naive"].dt.year.fillna(0).astype(int).astype(str)
        rev_by_year = (
            orders_df.groupby("year")["order_value"]
            .sum()
            .round(2)
            .sort_index()
            .to_dict()
        )

        # Revenue by Quarter
        orders_df["quarter"] = orders_df["purchase_dt_naive"].dt.to_period("Q").astype(str)
        rev_by_quarter = (
            orders_df.groupby("quarter")["order_value"]
            .sum()
            .round(2)
            .sort_index()
            .to_dict()
        )

        # Revenue by Month (YYYY-MM)
        orders_df["year_month"] = orders_df["purchase_dt_naive"].dt.to_period("M").astype(str)
        rev_by_month_series = orders_df.groupby("year_month")["order_value"].sum().round(2).sort_index()
        rev_by_month = rev_by_month_series.to_dict()

        # Month-over-Month (MoM) Growth Rate
        mom_growth_rates: Dict[str, float] = {}
        prev_rev: Optional[float] = None
        for ym, curr_rev in rev_by_month_series.items():
            if prev_rev is not None and prev_rev > 0:
                growth_pct = round(((curr_rev - prev_rev) / prev_rev * 100.0), 2)
                mom_growth_rates[str(ym)] = growth_pct
            else:
                mom_growth_rates[str(ym)] = 0.0
            prev_rev = curr_rev

        revenue_analysis = {
            "total_revenue": total_overall_revenue,
            "total_items_revenue": total_items_revenue,
            "total_freight_revenue": total_freight_revenue,
            "revenue_by_year": rev_by_year,
            "revenue_by_quarter": rev_by_quarter,
            "revenue_by_month": rev_by_month,
            "revenue_growth_rate": mom_growth_rates,
        }

        # ---------------------------------------------------------------------
        # 2. Order Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing order distribution by year, month, weekday, and hour...")

        orders_by_year = orders_df["year"].value_counts().sort_index().to_dict()
        orders_by_month = orders_df["year_month"].value_counts().sort_index().to_dict()

        # Orders by Weekday
        weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        orders_df["weekday_num"] = orders_df["purchase_dt_naive"].dt.weekday
        weekday_counts = orders_df["weekday_num"].value_counts().sort_index()
        orders_by_weekday = {
            weekday_names[int(day_idx)]: int(count)
            for day_idx, count in weekday_counts.items()
            if not np.isnan(day_idx) and 0 <= int(day_idx) <= 6
        }

        # Orders by Hour
        orders_df["hour"] = orders_df["purchase_dt_naive"].dt.hour
        hour_counts = orders_df["hour"].value_counts().sort_index()
        orders_by_hour = {
            f"{int(hr):02d}:00": int(cnt)
            for hr, cnt in hour_counts.items()
            if not np.isnan(hr)
        }

        # Average Order Value & Distribution Stats
        order_vals = orders_df["order_value"].dropna()
        aov = round(float(order_vals.mean()), 2) if len(order_vals) > 0 else 0.0

        order_val_stats = {
            "mean": aov,
            "std": round(float(order_vals.std()), 2) if len(order_vals) > 1 else 0.0,
            "min": round(float(order_vals.min()), 2) if len(order_vals) > 0 else 0.0,
            "q25": round(float(order_vals.quantile(0.25)), 2) if len(order_vals) > 0 else 0.0,
            "median": round(float(order_vals.median()), 2) if len(order_vals) > 0 else 0.0,
            "q75": round(float(order_vals.quantile(0.75)), 2) if len(order_vals) > 0 else 0.0,
            "max": round(float(order_vals.max()), 2) if len(order_vals) > 0 else 0.0,
            "skewness": round(float(order_vals.skew()), 4) if len(order_vals) > 2 else 0.0,
        }

        order_analysis = {
            "orders_by_year": orders_by_year,
            "orders_by_month": orders_by_month,
            "orders_by_weekday": orders_by_weekday,
            "orders_by_hour": orders_by_hour,
            "average_order_value": aov,
            "distribution_of_order_values": order_val_stats,
        }

        # ---------------------------------------------------------------------
        # 3. Seasonality
        # ---------------------------------------------------------------------
        logger.info("Evaluating seasonality patterns and detecting holiday sales spikes...")

        # Calendar month seasonality (Jan-Dec aggregated across all years)
        month_names = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]
        orders_df["cal_month"] = orders_df["purchase_dt_naive"].dt.month
        monthly_seasonality_df = orders_df.groupby("cal_month").agg(
            total_revenue=("order_value", "sum"),
            avg_revenue=("order_value", "mean"),
            order_count=("order_id", "count"),
        ).reset_index()

        monthly_seasonality = {
            month_names[int(row["cal_month"]) - 1]: {
                "total_revenue": round(float(row["total_revenue"]), 2),
                "average_revenue": round(float(row["avg_revenue"]), 2),
                "order_count": int(row["order_count"]),
            }
            for _, row in monthly_seasonality_df.iterrows()
            if 1 <= int(row["cal_month"]) <= 12
        }

        # Calendar quarter seasonality (Q1-Q4 aggregated across all years)
        orders_df["cal_quarter"] = orders_df["purchase_dt_naive"].dt.quarter
        quarterly_seasonality_df = orders_df.groupby("cal_quarter").agg(
            total_revenue=("order_value", "sum"),
            avg_revenue=("order_value", "mean"),
            order_count=("order_id", "count"),
        ).reset_index()

        quarterly_seasonality = {
            f"Q{int(row['cal_quarter'])}": {
                "total_revenue": round(float(row["total_revenue"]), 2),
                "average_revenue": round(float(row["avg_revenue"]), 2),
                "order_count": int(row["order_count"]),
            }
            for _, row in quarterly_seasonality_df.iterrows()
            if 1 <= int(row["cal_quarter"]) <= 4
        }

        # Holiday & Peak Spike Detection (daily sales analysis)
        orders_df["date_str"] = orders_df["purchase_dt_naive"].dt.strftime("%Y-%m-%d")
        daily_sales = orders_df.groupby("date_str").agg(
            daily_revenue=("order_value", "sum"),
            daily_orders=("order_id", "count"),
        ).reset_index()

        mean_daily_rev = float(daily_sales["daily_revenue"].mean()) if len(daily_sales) > 0 else 0.0
        std_daily_rev = float(daily_sales["daily_revenue"].std()) if len(daily_sales) > 1 else 0.0
        spike_threshold = mean_daily_rev + (3.0 * std_daily_rev)

        top_spike_days = daily_sales.sort_values(by="daily_revenue", ascending=False).head(10)
        detected_spikes = []
        for _, row in top_spike_days.iterrows():
            d_str = str(row["date_str"])
            d_rev = round(float(row["daily_revenue"]), 2)
            d_ords = int(row["daily_orders"])
            ratio_vs_avg = round((d_rev / mean_daily_rev), 2) if mean_daily_rev > 0 else 0.0
            
            # Identify holiday context if matching known major shopping dates
            event_tag = "Standard Peak"
            if "2017-11-24" in d_str or "2017-11-25" in d_str:
                event_tag = "Black Friday 2017"
            elif "2016-11-25" in d_str:
                event_tag = "Black Friday 2016"
            elif "2017-11-27" in d_str or "2018-11-26" in d_str:
                event_tag = "Cyber Monday"
            elif d_rev >= spike_threshold:
                event_tag = "Statistical Spike (>3 Sigma)"

            detected_spikes.append({
                "date": d_str,
                "daily_revenue": d_rev,
                "daily_orders": d_ords,
                "revenue_multiplier_vs_avg": ratio_vs_avg,
                "event_context": event_tag,
            })

        seasonality = {
            "monthly_seasonality": monthly_seasonality,
            "quarterly_seasonality": quarterly_seasonality,
            "holiday_spike_detection": {
                "average_daily_revenue": round(mean_daily_rev, 2),
                "spike_threshold_3_sigma": round(spike_threshold, 2),
                "top_revenue_spike_days": detected_spikes,
            },
        }

        # ---------------------------------------------------------------------
        # 4. Sales Performance
        # ---------------------------------------------------------------------
        logger.info("Evaluating highest/lowest revenue months, categories, and concentration...")

        month_perf_df = orders_df.groupby("year_month").agg(
            revenue=("order_value", "sum"),
            order_count=("order_id", "count"),
        ).reset_index()

        # Exclude incomplete tail/head months with < 10 orders if any
        valid_months = month_perf_df[month_perf_df["order_count"] >= 10]
        if len(valid_months) == 0:
            valid_months = month_perf_df

        highest_rev_months = (
            valid_months.sort_values(by="revenue", ascending=False)
            .head(5)
            .apply(lambda r: {"year_month": str(r["year_month"]), "revenue": round(float(r["revenue"]), 2), "order_count": int(r["order_count"])}, axis=1)
            .tolist()
        )

        lowest_rev_months = (
            valid_months.sort_values(by="revenue", ascending=True)
            .head(5)
            .apply(lambda r: {"year_month": str(r["year_month"]), "revenue": round(float(r["revenue"]), 2), "order_count": int(r["order_count"])}, axis=1)
            .tolist()
        )

        # Best selling categories
        merged_items = order_items_df.merge(
            products_df[["product_id", "category_name_english", "product_category_name"]],
            on="product_id",
            how="left",
        )
        merged_items["effective_category"] = (
            merged_items["category_name_english"]
            .fillna(merged_items["product_category_name"])
            .fillna("Uncategorized")
        )

        best_selling_categories = (
            merged_items.groupby("effective_category")["price"]
            .sum()
            .sort_values(ascending=False)
            .head(20)
            .round(2)
            .to_dict()
        )

        # Revenue Concentration (Pareto analysis on products)
        prod_rev = order_items_df.groupby("product_id")["price"].sum().sort_values(ascending=False)
        total_prod_rev = prod_rev.sum()
        total_prod_cnt = len(prod_rev)

        def _calc_top_pct_contribution(top_pct: float) -> float:
            if total_prod_cnt == 0 or total_prod_rev == 0:
                return 0.0
            n_items = max(1, int(np.ceil(total_prod_cnt * (top_pct / 100.0))))
            top_rev_sum = float(prod_rev.head(n_items).sum())
            return round((top_rev_sum / total_prod_rev * 100.0), 2)

        revenue_concentration = {
            "top_1_percent_products_revenue_share": _calc_top_pct_contribution(1.0),
            "top_5_percent_products_revenue_share": _calc_top_pct_contribution(5.0),
            "top_10_percent_products_revenue_share": _calc_top_pct_contribution(10.0),
            "top_20_percent_products_revenue_share": _calc_top_pct_contribution(20.0),
        }

        sales_performance = {
            "highest_revenue_months": highest_rev_months,
            "lowest_revenue_months": lowest_rev_months,
            "best_selling_categories": best_selling_categories,
            "revenue_concentration": revenue_concentration,
        }

        # ---------------------------------------------------------------------
        # 5. Operational Metrics
        # ---------------------------------------------------------------------
        logger.info("Computing operational metrics (items/order, freight %, revenue/customer)...")

        avg_items_per_order = round(float(orders_df["order_items_qty"].mean()), 2) if total_orders > 0 else 0.0
        freight_percentage = (
            round((total_freight_revenue / total_overall_revenue * 100.0), 2)
            if total_overall_revenue > 0
            else 0.0
        )
        revenue_per_order = round((total_overall_revenue / total_orders), 2) if total_orders > 0 else 0.0

        # Unique customers
        total_unique_custs = int(customers_df["customer_unique_id"].nunique())
        revenue_per_customer = (
            round((total_overall_revenue / total_unique_custs), 2)
            if total_unique_custs > 0
            else 0.0
        )

        operational_metrics = {
            "average_items_per_order": avg_items_per_order,
            "freight_percentage_of_total_revenue": freight_percentage,
            "revenue_per_order": revenue_per_order,
            "revenue_per_customer": revenue_per_customer,
            "total_unique_customers_count": total_unique_custs,
        }

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Sales EDA in {elapsed_sec:.4f}s.")

        report = SalesAnalysisReport(
            total_orders_analyzed=total_orders,
            revenue_analysis=revenue_analysis,
            order_analysis=order_analysis,
            seasonality=seasonality,
            sales_performance=sales_performance,
            operational_metrics=operational_metrics,
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save JSON artifact to artifacts/eda/sales_analysis.json
        report.save_json()

        return report
