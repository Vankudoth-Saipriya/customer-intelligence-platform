"""
Product Exploratory Data Analysis (EDA) module.

Performs product category analysis, product dimension evaluation,
performance metrics computation, freight cost analysis, and translation coverage tracking.
"""

import time
from typing import Any, Dict, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data_loader import AnalyticsDataLoader
from app.analytics.data_profiler import DataProfiler
from app.eda.report import ProductAnalysisReport


class ProductAnalyzer:
    """
    Analyzer executing comprehensive Product EDA and generating structured reports.
    """

    def __init__(
        self,
        data_loader: Optional[AnalyticsDataLoader] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Initialize ProductAnalyzer with data loader or session.
        """
        self.data_loader = data_loader or AnalyticsDataLoader(session=session)
        self.profiler = DataProfiler()

    def analyze(self) -> ProductAnalysisReport:
        """
        Execute full product exploratory data analysis.

        Returns:
            ProductAnalysisReport containing analytical statistics.
        """
        start_time = time.perf_counter()
        logger.info("Initiating Product Exploratory Data Analysis (EDA)...")

        # Load product and order_items datasets via AnalyticsDataLoader
        products_df = self.data_loader.load_products()
        order_items_df = self.data_loader.load_order_items()

        total_products = len(products_df)
        logger.info(f"Loaded {total_products:,} product records for EDA.")

        # Determine effective category column (prefer English translation, fallback to Portuguese, or 'Uncategorized')
        effective_cat = products_df["category_name_english"].fillna(products_df["product_category_name"]).fillna("Uncategorized")
        products_df["effective_category"] = effective_cat

        # ---------------------------------------------------------------------
        # 1. Product Category Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing product category distribution, revenue, and order counts...")

        prod_count_by_cat = products_df["effective_category"].value_counts()
        products_per_category = prod_count_by_cat.to_dict()
        top_20_categories = prod_count_by_cat.head(20).to_dict()

        # Merge order items with products for revenue and order count by category
        merged_items = order_items_df.merge(
            products_df[["product_id", "effective_category", "product_weight_g", "product_volume_cm3"]],
            on="product_id",
            how="left",
        )
        merged_items["effective_category"] = merged_items["effective_category"].fillna("Uncategorized")

        # Revenue by category
        revenue_by_cat_series = merged_items.groupby("effective_category")["price"].sum().round(2)
        revenue_by_category = revenue_by_cat_series.to_dict()

        # Order item count by category
        item_count_by_cat_series = merged_items.groupby("effective_category")["order_id"].count()
        order_count_by_category = item_count_by_cat_series.to_dict()

        category_analysis = {
            "products_per_category": products_per_category,
            "top_20_categories": top_20_categories,
            "revenue_by_category": revenue_by_category,
            "order_count_by_category": order_count_by_category,
        }

        # ---------------------------------------------------------------------
        # 2. Product Dimension Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing product physical dimensions and detecting outliers...")

        def _calc_distribution(series: pd.Series) -> Dict[str, Any]:
            clean_s = series.dropna()
            if len(clean_s) == 0:
                return {}
            return {
                "mean": round(float(clean_s.mean()), 2),
                "std": round(float(clean_s.std()), 2) if len(clean_s) > 1 else 0.0,
                "min": round(float(clean_s.min()), 2),
                "q25": round(float(clean_s.quantile(0.25)), 2),
                "median": round(float(clean_s.median()), 2),
                "q75": round(float(clean_s.quantile(0.75)), 2),
                "max": round(float(clean_s.max()), 2),
                "skewness": round(float(clean_s.skew()), 4) if len(clean_s) > 2 else 0.0,
                "null_count": int(series.isnull().sum()),
            }

        def _detect_outliers(series: pd.Series) -> Dict[str, Any]:
            clean_s = series.dropna()
            if len(clean_s) == 0:
                return {"outlier_count": 0, "outlier_percentage": 0.0, "lower_bound": 0.0, "upper_bound": 0.0}
            q1 = float(clean_s.quantile(0.25))
            q3 = float(clean_s.quantile(0.75))
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            outlier_mask = (clean_s < lower_bound) | (clean_s > upper_bound)
            outlier_cnt = int(outlier_mask.sum())
            outlier_pct = round((outlier_cnt / len(clean_s) * 100.0), 2)
            return {
                "outlier_count": outlier_cnt,
                "outlier_percentage": outlier_pct,
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
            }

        weight_dist = _calc_distribution(products_df["product_weight_g"])
        volume_dist = _calc_distribution(products_df["product_volume_cm3"])
        length_stats = _calc_distribution(products_df["product_length_cm"])
        width_stats = _calc_distribution(products_df["product_width_cm"])
        height_stats = _calc_distribution(products_df["product_height_cm"])

        outliers_summary = {
            "weight_g": _detect_outliers(products_df["product_weight_g"]),
            "volume_cm3": _detect_outliers(products_df["product_volume_cm3"]),
            "length_cm": _detect_outliers(products_df["product_length_cm"]),
            "width_cm": _detect_outliers(products_df["product_width_cm"]),
            "height_cm": _detect_outliers(products_df["product_height_cm"]),
        }

        dimension_analysis = {
            "weight_distribution": weight_dist,
            "volume_distribution": volume_dist,
            "dimension_statistics": {
                "length_cm": length_stats,
                "width_cm": width_stats,
                "height_cm": height_stats,
            },
            "outliers": outliers_summary,
        }

        # ---------------------------------------------------------------------
        # 3. Product Performance Analysis
        # ---------------------------------------------------------------------
        logger.info("Evaluating product performance, top sellers, and revenue stats...")

        perf_grouped = order_items_df.groupby("product_id").agg(
            items_sold=("order_item_id", "count"),
            total_revenue=("price", "sum"),
            distinct_orders=("order_id", "nunique"),
        ).reset_index()

        perf_merged = perf_grouped.merge(
            products_df[["product_id", "effective_category"]],
            on="product_id",
            how="left",
        )

        top_by_revenue = perf_merged.sort_values(by="total_revenue", ascending=False).head(20)
        top_by_units = perf_merged.sort_values(by="items_sold", ascending=False).head(20)

        top_selling_products_rev = [
            {
                "product_id": str(row["product_id"]),
                "category": str(row["effective_category"]),
                "items_sold": int(row["items_sold"]),
                "total_revenue": round(float(row["total_revenue"]), 2),
                "distinct_orders": int(row["distinct_orders"]),
            }
            for _, row in top_by_revenue.iterrows()
        ]

        top_selling_products_units = [
            {
                "product_id": str(row["product_id"]),
                "category": str(row["effective_category"]),
                "items_sold": int(row["items_sold"]),
                "total_revenue": round(float(row["total_revenue"]), 2),
                "distinct_orders": int(row["distinct_orders"]),
            }
            for _, row in top_by_units.iterrows()
        ]

        top_selling_categories = (
            merged_items.groupby("effective_category")["price"]
            .sum()
            .sort_values(ascending=False)
            .round(2)
            .to_dict()
        )

        sold_product_ids = set(order_items_df["product_id"].unique())
        all_product_ids = set(products_df["product_id"].unique())
        no_sales_ids = sorted(list(all_product_ids - sold_product_ids))
        no_sales_count = len(no_sales_ids)
        no_sales_pct = round((no_sales_count / total_products * 100.0), 2) if total_products > 0 else 0.0

        rev_per_product_stats = _calc_distribution(perf_grouped["total_revenue"])

        product_performance = {
            "top_selling_products_by_revenue": top_selling_products_rev,
            "top_selling_products_by_units": top_selling_products_units,
            "top_selling_categories": top_selling_categories,
            "products_with_no_sales": {
                "count": no_sales_count,
                "percentage": no_sales_pct,
                "sample_product_ids": no_sales_ids[:10],
            },
            "revenue_per_product_stats": rev_per_product_stats,
        }

        # ---------------------------------------------------------------------
        # 4. Freight Analysis
        # ---------------------------------------------------------------------
        logger.info("Analyzing freight costs and correlations with dimensions...")

        freight_by_cat = (
            merged_items.groupby("effective_category")["freight_value"]
            .agg(["mean", "median", "sum", "count"])
            .rename(columns={"mean": "avg_freight", "median": "median_freight", "sum": "total_freight", "count": "order_items_count"})
            .round(2)
            .to_dict(orient="index")
        )

        valid_freight_weight = merged_items[["freight_value", "product_weight_g"]].dropna()
        freight_vs_weight_corr = (
            round(float(valid_freight_weight["freight_value"].corr(valid_freight_weight["product_weight_g"])), 4)
            if len(valid_freight_weight) > 1
            else 0.0
        )

        valid_freight_volume = merged_items[["freight_value", "product_volume_cm3"]].dropna()
        freight_vs_volume_corr = (
            round(float(valid_freight_volume["freight_value"].corr(valid_freight_volume["product_volume_cm3"])), 4)
            if len(valid_freight_volume) > 1
            else 0.0
        )

        freight_analysis = {
            "freight_value_by_category": freight_by_cat,
            "freight_vs_product_weight_correlation": freight_vs_weight_corr,
            "freight_vs_product_volume_correlation": freight_vs_volume_corr,
        }

        # ---------------------------------------------------------------------
        # 5. Translation Coverage
        # ---------------------------------------------------------------------
        logger.info("Evaluating Portuguese-to-English translation coverage...")

        pt_categories = products_df["product_category_name"].dropna().unique()
        total_pt_categories = len(pt_categories)

        translated_categories = (
            products_df[["product_category_name", "category_name_english"]]
            .dropna()
            .drop_duplicates()
        )
        translated_cat_count = len(translated_categories)

        missing_cat_df = products_df[products_df["product_category_name"].notnull() & products_df["category_name_english"].isnull()]
        missing_cat_list = sorted(missing_cat_df["product_category_name"].unique().tolist())
        missing_cat_count = len(missing_cat_list)

        cat_coverage_pct = round((translated_cat_count / total_pt_categories * 100.0), 2) if total_pt_categories > 0 else 0.0

        prods_with_translation = int(products_df["category_name_english"].notnull().sum())
        prod_coverage_pct = round((prods_with_translation / total_products * 100.0), 2) if total_products > 0 else 0.0

        translation_coverage = {
            "total_pt_categories": total_pt_categories,
            "categories_with_english_translation": translated_cat_count,
            "missing_translations_count": missing_cat_count,
            "missing_translation_categories": missing_cat_list,
            "category_translation_coverage_percent": cat_coverage_pct,
            "product_translation_coverage_percent": prod_coverage_pct,
        }

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Product EDA in {elapsed_sec:.4f}s.")

        report = ProductAnalysisReport(
            total_products_analyzed=total_products,
            category_analysis=category_analysis,
            dimension_analysis=dimension_analysis,
            product_performance=product_performance,
            freight_analysis=freight_analysis,
            translation_coverage=translation_coverage,
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save JSON artifact to artifacts/eda/product_analysis.json
        report.save_json()

        return report
