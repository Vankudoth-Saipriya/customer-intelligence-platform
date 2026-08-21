"""
Customer Feature Store Module.

Engineers scalable, modular customer-level features across 8 feature groups:
1. Customer Profile
2. RFM Features
3. Purchase Behaviour
4. Payment Features
5. Delivery Features
6. Review Features
7. Revenue Features
8. Derived Features

Outputs Parquet, CSV, and JSON metadata artifacts.
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.analytics.data_loader import AnalyticsDataLoader
from app.features.report import CustomerFeatureStoreReport


class CustomerFeatureStore:
    """
    Feature Store engine aggregating domain tables into a unified 1-row-per-customer feature table.
    """

    def __init__(
        self,
        data_loader: Optional[AnalyticsDataLoader] = None,
        session: Optional[Session] = None,
    ) -> None:
        """
        Initialize CustomerFeatureStore with data loader or session.
        """
        self.data_loader = data_loader or AnalyticsDataLoader(session=session)

    def build_feature_store(
        self,
        output_dir: Optional[Path] = None,
    ) -> CustomerFeatureStoreReport:
        """
        Execute feature engineering pipeline and export artifacts.

        Returns:
            CustomerFeatureStoreReport detailing generated features.
        """
        start_time = time.perf_counter()
        logger.info("Initiating Customer Feature Store Engineering Pipeline...")

        # 1. Load domain datasets via AnalyticsDataLoader
        customers_df = self.data_loader.load_customers()
        orders_df = self.data_loader.load_orders()
        order_items_df = self.data_loader.load_order_items()
        products_df = self.data_loader.load_products()
        payments_df = self.data_loader.load_payments()
        reviews_df = self.data_loader.load_reviews()

        logger.info(f"Loaded source datasets. Raw customers: {len(customers_df):,} rows.")

        # Ensure datetime dtypes
        orders_df["purchase_dt"] = pd.to_datetime(orders_df["order_purchase_timestamp"], errors="coerce", utc=True)
        orders_df["deliv_dt"] = pd.to_datetime(orders_df["order_delivered_customer_date"], errors="coerce", utc=True)
        orders_df["estim_dt"] = pd.to_datetime(orders_df["order_estimated_delivery_date"], errors="coerce", utc=True)

        # Merge orders with customers to link customer_unique_id
        cust_map = customers_df[["customer_id", "customer_unique_id", "customer_state", "customer_city"]].drop_duplicates(subset=["customer_id"])
        orders_merged = orders_df.merge(cust_map, on="customer_id", how="left")

        # Reference max date in dataset for recency & age calculation
        max_dt = orders_merged["purchase_dt"].max()

        # ---------------------------------------------------------------------
        # Group 1 & 2: Base Customer Profile, Orders Aggregation, and RFM Features
        # ---------------------------------------------------------------------
        logger.info("Engineering Customer Profile & RFM features per unique customer...")

        orders_merged["deliv_days"] = (orders_merged["deliv_dt"] - orders_merged["purchase_dt"]).dt.total_seconds() / 86400.0
        orders_merged["delay_days"] = (orders_merged["deliv_dt"] - orders_merged["estim_dt"]).dt.total_seconds() / 86400.0

        # Sort by purchase date for order sequence calculations
        orders_merged = orders_merged.sort_values(by=["customer_unique_id", "purchase_dt"])

        # Calculate time between consecutive orders
        orders_merged["prev_purchase_dt"] = orders_merged.groupby("customer_unique_id")["purchase_dt"].shift(1)
        orders_merged["days_since_prev_order"] = (orders_merged["purchase_dt"] - orders_merged["prev_purchase_dt"]).dt.total_seconds() / 86400.0

        cust_profile = orders_merged.groupby("customer_unique_id").agg(
            state=("customer_state", "last"),
            city=("customer_city", "last"),
            first_purchase_dt=("purchase_dt", "min"),
            last_purchase_dt=("purchase_dt", "max"),
            frequency_orders=("order_id", "nunique"),
            monetary_value=("order_value", "sum"),
            total_items=("order_items_qty", "sum"),
            avg_freight_value=("total_freight_value", "mean"),
            avg_delivery_days=("deliv_days", "mean"),
            avg_delivery_delay=("delay_days", "mean"),
            late_order_count=("delay_days", lambda s: (s > 0).sum()),
            delivered_order_count=("deliv_dt", "count"),
            days_between_orders_mean=("days_since_prev_order", "mean"),
            order_value_std=("order_value", "std"),
        ).reset_index()

        # Handle full customer coverage across unique customers
        unique_cust_base = customers_df[["customer_unique_id", "customer_state", "customer_city"]].drop_duplicates(subset=["customer_unique_id"]).copy()
        feature_df = unique_cust_base.merge(cust_profile, on="customer_unique_id", how="left")

        feature_df["state"] = feature_df["state"].fillna(feature_df["customer_state"])
        feature_df["city"] = feature_df["city"].fillna(feature_df["customer_city"])
        feature_df = feature_df.drop(columns=["customer_state", "customer_city"])

        # Customer ID alias
        feature_df["customer_id"] = feature_df["customer_unique_id"]

        feature_df["first_purchase_date"] = feature_df["first_purchase_dt"].dt.strftime("%Y-%m-%d")
        feature_df["last_purchase_date"] = feature_df["last_purchase_dt"].dt.strftime("%Y-%m-%d")

        feature_df["customer_age_days"] = (
            (max_dt - feature_df["first_purchase_dt"]).dt.total_seconds() / 86400.0
        ).fillna(0.0).round(2)

        feature_df["recency_days"] = (
            (max_dt - feature_df["last_purchase_dt"]).dt.total_seconds() / 86400.0
        ).fillna(999.0).round(2)

        feature_df["frequency_orders"] = feature_df["frequency_orders"].fillna(0).astype(int)
        feature_df["monetary_value"] = feature_df["monetary_value"].fillna(0.0).round(2)

        feature_df["avg_order_value"] = np.where(
            feature_df["frequency_orders"] > 0,
            (feature_df["monetary_value"] / feature_df["frequency_orders"]).round(2),
            0.0,
        )

        # ---------------------------------------------------------------------
        # Group 3: Purchase Behaviour
        # ---------------------------------------------------------------------
        logger.info("Engineering Purchase Behaviour features...")

        feature_df["total_items"] = feature_df["total_items"].fillna(0).astype(int)
        feature_df["avg_items_per_order"] = np.where(
            feature_df["frequency_orders"] > 0,
            (feature_df["total_items"] / feature_df["frequency_orders"]).round(2),
            0.0,
        )

        items_merged = order_items_df.merge(orders_merged[["order_id", "customer_unique_id"]], on="order_id", how="left")
        items_merged = items_merged.merge(products_df[["product_id", "category_name_english", "product_category_name"]], on="product_id", how="left")
        items_merged["effective_category"] = items_merged["category_name_english"].fillna(items_merged["product_category_name"]).fillna("Uncategorized")

        cat_fav = (
            items_merged.groupby(["customer_unique_id", "effective_category"])["order_item_id"]
            .count()
            .reset_index()
            .sort_values(by=["customer_unique_id", "order_item_id"], ascending=[True, False])
            .drop_duplicates(subset=["customer_unique_id"])
            .rename(columns={"effective_category": "favorite_product_category"})
        )

        cat_unique = (
            items_merged.groupby("customer_unique_id")["effective_category"]
            .nunique()
            .reset_index()
            .rename(columns={"effective_category": "unique_categories"})
        )

        feature_df = feature_df.merge(cat_fav[["customer_unique_id", "favorite_product_category"]], on="customer_unique_id", how="left")
        feature_df = feature_df.merge(cat_unique, on="customer_unique_id", how="left")

        feature_df["favorite_product_category"] = feature_df["favorite_product_category"].fillna("Uncategorized")
        feature_df["unique_categories"] = feature_df["unique_categories"].fillna(0).astype(int)

        feature_df["repeat_purchase_rate"] = np.where(
            feature_df["frequency_orders"] > 1,
            ((feature_df["frequency_orders"] - 1) / feature_df["frequency_orders"]).round(4),
            0.0,
        )

        # ---------------------------------------------------------------------
        # Group 4: Payment Features
        # ---------------------------------------------------------------------
        logger.info("Engineering Payment features...")

        pmts_merged = payments_df.merge(orders_merged[["order_id", "customer_unique_id"]], on="order_id", how="left")

        pmt_agg = pmts_merged.groupby("customer_unique_id").agg(
            avg_payment_value=("payment_value", "mean"),
            avg_installments=("payment_installments", "mean"),
            total_pmt_count=("payment_sequential", "count"),
            installment_pmt_count=("payment_installments", lambda s: (s > 1).sum()),
            voucher_pmt_count=("payment_type", lambda s: (s == "voucher").sum()),
        ).reset_index()

        preferred_pmt = (
            pmts_merged.groupby(["customer_unique_id", "payment_type"])["payment_sequential"]
            .count()
            .reset_index()
            .sort_values(by=["customer_unique_id", "payment_sequential"], ascending=[True, False])
            .drop_duplicates(subset=["customer_unique_id"])
            .rename(columns={"payment_type": "preferred_payment_method"})
        )

        feature_df = feature_df.merge(pmt_agg, on="customer_unique_id", how="left")
        feature_df = feature_df.merge(preferred_pmt[["customer_unique_id", "preferred_payment_method"]], on="customer_unique_id", how="left")

        feature_df["preferred_payment_method"] = feature_df["preferred_payment_method"].fillna("Uncategorized")
        feature_df["avg_payment_value"] = feature_df["avg_payment_value"].fillna(0.0).round(2)
        feature_df["avg_installments"] = feature_df["avg_installments"].fillna(0.0).round(2)

        feature_df["installment_ratio"] = np.where(
            feature_df["total_pmt_count"] > 0,
            (feature_df["installment_pmt_count"] / feature_df["total_pmt_count"]).round(4),
            0.0,
        )

        feature_df["voucher_usage_ratio"] = np.where(
            feature_df["total_pmt_count"] > 0,
            (feature_df["voucher_pmt_count"] / feature_df["total_pmt_count"]).round(4),
            0.0,
        )

        feature_df = feature_df.drop(columns=["total_pmt_count", "installment_pmt_count", "voucher_pmt_count"], errors="ignore")

        # ---------------------------------------------------------------------
        # Group 5: Delivery Features
        # ---------------------------------------------------------------------
        logger.info("Engineering Delivery features...")

        feature_df["avg_delivery_days"] = feature_df["avg_delivery_days"].fillna(0.0).round(2)
        feature_df["avg_delivery_delay"] = feature_df["avg_delivery_delay"].fillna(0.0).round(2)
        feature_df["avg_freight_value"] = feature_df["avg_freight_value"].fillna(0.0).round(2)

        feature_df["late_delivery_ratio"] = np.where(
            feature_df["delivered_order_count"] > 0,
            (feature_df["late_order_count"] / feature_df["delivered_order_count"]).round(4),
            0.0,
        )

        feature_df = feature_df.drop(columns=["late_order_count", "delivered_order_count"], errors="ignore")

        # ---------------------------------------------------------------------
        # Group 6: Review Features
        # ---------------------------------------------------------------------
        logger.info("Engineering Review features...")

        reviews_merged = reviews_df.merge(orders_merged[["order_id", "customer_unique_id"]], on="order_id", how="left")

        rev_agg = reviews_merged.groupby("customer_unique_id").agg(
            avg_review_score=("review_score", "mean"),
            review_count=("review_id", "count"),
            positive_rev_cnt=("review_score", lambda s: (s >= 4).sum()),
            negative_rev_cnt=("review_score", lambda s: (s <= 2).sum()),
        ).reset_index()

        feature_df = feature_df.merge(rev_agg, on="customer_unique_id", how="left")

        feature_df["avg_review_score"] = feature_df["avg_review_score"].fillna(0.0).round(2)
        feature_df["review_count"] = feature_df["review_count"].fillna(0).astype(int)

        feature_df["positive_review_ratio"] = np.where(
            feature_df["review_count"] > 0,
            (feature_df["positive_rev_cnt"] / feature_df["review_count"]).round(4),
            0.0,
        )

        feature_df["negative_review_ratio"] = np.where(
            feature_df["review_count"] > 0,
            (feature_df["negative_rev_cnt"] / feature_df["review_count"]).round(4),
            0.0,
        )

        feature_df = feature_df.drop(columns=["positive_rev_cnt", "negative_rev_cnt"], errors="ignore")

        # ---------------------------------------------------------------------
        # Group 7: Revenue Features
        # ---------------------------------------------------------------------
        logger.info("Engineering Revenue features & value segmentation tiers...")

        feature_df["total_revenue"] = feature_df["monetary_value"]
        feature_df["revenue_rank_percentile"] = (
            feature_df["total_revenue"].rank(pct=True) * 100.0
        ).round(2)

        q25_val = feature_df["total_revenue"].quantile(0.25)
        q75_val = feature_df["total_revenue"].quantile(0.75)

        tier_conditions = [
            (feature_df["total_revenue"] > q75_val),
            (feature_df["total_revenue"] > q25_val) & (feature_df["total_revenue"] <= q75_val),
            (feature_df["total_revenue"] <= q25_val),
        ]
        tier_choices = ["High Value", "Medium Value", "Low Value"]
        feature_df["customer_value_tier"] = np.select(tier_conditions, tier_choices, default="Low Value")

        # ---------------------------------------------------------------------
        # Group 8: Derived Features
        # ---------------------------------------------------------------------
        logger.info("Engineering Derived features...")

        feature_df["days_between_orders_mean"] = feature_df["days_between_orders_mean"].fillna(0.0).round(2)
        feature_df["order_value_std"] = feature_df["order_value_std"].fillna(0.0).round(2)

        lifespan_months = np.maximum(1.0, feature_df["customer_age_days"] / 30.44)
        feature_df["spending_velocity"] = (feature_df["total_revenue"] / lifespan_months).round(2)
        feature_df["order_frequency_per_month"] = (feature_df["frequency_orders"] / lifespan_months).round(4)

        feature_df = feature_df.drop(columns=["first_purchase_dt", "last_purchase_dt"], errors="ignore")

        feature_groups: Dict[str, List[str]] = {
            "customer_profile": ["customer_id", "customer_unique_id", "state", "city", "customer_age_days", "first_purchase_date", "last_purchase_date"],
            "rfm_features": ["recency_days", "frequency_orders", "monetary_value", "avg_order_value"],
            "purchase_behaviour": ["total_items", "avg_items_per_order", "favorite_product_category", "unique_categories", "repeat_purchase_rate"],
            "payment_features": ["preferred_payment_method", "avg_payment_value", "avg_installments", "installment_ratio", "voucher_usage_ratio"],
            "delivery_features": ["avg_delivery_days", "avg_delivery_delay", "late_delivery_ratio", "avg_freight_value"],
            "review_features": ["avg_review_score", "positive_review_ratio", "negative_review_ratio", "review_count"],
            "revenue_features": ["total_revenue", "revenue_rank_percentile", "customer_value_tier"],
            "derived_features": ["days_between_orders_mean", "order_value_std", "spending_velocity", "order_frequency_per_month"],
        }

        all_cols = []
        for grp_cols in feature_groups.values():
            all_cols.extend(grp_cols)

        feature_df = feature_df[all_cols].copy()

        num_cols = feature_df.select_dtypes(include=[np.number]).columns
        feature_df[num_cols] = feature_df[num_cols].fillna(0.0)

        str_cols = feature_df.select_dtypes(include=["object", "string"]).columns
        feature_df[str_cols] = feature_df[str_cols].fillna("Unknown")

        total_custs = len(feature_df)
        total_feats = len(feature_df.columns)
        logger.info(f"Built Feature Store DataFrame shape: {feature_df.shape} across {total_custs:,} unique customers.")

        # ---------------------------------------------------------------------
        # Export Artifacts (Parquet, CSV, JSON Metadata)
        # ---------------------------------------------------------------------
        if output_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "features"
        else:
            target_dir = Path(output_dir)

        target_dir.mkdir(parents=True, exist_ok=True)

        parquet_path = target_dir / "customer_feature_store.parquet"
        csv_path = target_dir / "customer_feature_store.csv"

        logger.info(f"Exporting Parquet feature store artifact -> '{parquet_path.resolve()}'")
        feature_df.to_parquet(parquet_path, index=False, engine="pyarrow")

        logger.info(f"Exporting CSV feature store artifact -> '{csv_path.resolve()}'")
        feature_df.to_csv(csv_path, index=False)

        col_types = {col: str(dtype) for col, dtype in feature_df.dtypes.items()}

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Feature Store Engineering in {elapsed_sec:.4f}s.")

        report = CustomerFeatureStoreReport(
            total_customers=total_custs,
            total_features=total_feats,
            feature_groups=feature_groups,
            parquet_path=str(parquet_path.resolve()),
            csv_path=str(csv_path.resolve()),
            metadata_path="",
            column_types=col_types,
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save metadata report to artifacts/features/customer_feature_store_metadata.json
        report.save_json()

        return report

    def build_temporal_feature_store(
        self,
        cutoff_date: str = "2017-10-01",
        output_dir: Optional[Path] = None,
    ) -> pd.DataFrame:
        """
        Build temporal feature store with strict observation cutoff date to eliminate target leakage.
        Predictors ($X$) are computed strictly from orders placed BEFORE cutoff_date.
        Targets ($y$) are computed strictly from orders placed ON OR AFTER cutoff_date.
        """
        start_time = time.perf_counter()
        cutoff_dt = pd.to_datetime(cutoff_date, utc=True)
        logger.info(f"Engineering Temporal Customer Feature Store with Cutoff Date: '{cutoff_date}'...")

        customers_df = self.data_loader.load_customers()
        orders_df = self.data_loader.load_orders()
        order_items_df = self.data_loader.load_order_items()
        payments_df = self.data_loader.load_payments()
        reviews_df = self.data_loader.load_reviews()

        orders_df["purchase_dt"] = pd.to_datetime(orders_df["order_purchase_timestamp"], errors="coerce", utc=True)
        orders_df["deliv_dt"] = pd.to_datetime(orders_df["order_delivered_customer_date"], errors="coerce", utc=True)
        orders_df["estim_dt"] = pd.to_datetime(orders_df["order_estimated_delivery_date"], errors="coerce", utc=True)

        cust_map = customers_df[["customer_id", "customer_unique_id", "customer_state", "customer_city"]].drop_duplicates(subset=["customer_id"])
        orders_merged = orders_df.merge(cust_map, on="customer_id", how="left")

        # Order price & freight item aggregations
        items_agg = order_items_df.groupby("order_id").agg(
            order_price=("price", "sum"),
            order_freight=("freight_value", "sum"),
            items_qty=("order_item_id", "count"),
        ).reset_index()

        orders_merged = orders_merged.merge(items_agg, on="order_id", how="left")
        orders_merged["order_price"] = orders_merged["order_price"].fillna(0.0)
        orders_merged["order_freight"] = orders_merged["order_freight"].fillna(0.0)
        orders_merged["items_qty"] = orders_merged["items_qty"].fillna(0).astype(int)
        orders_merged["order_value"] = orders_merged["order_price"] + orders_merged["order_freight"]

        # Filter observation orders (< cutoff_date) and future orders (>= cutoff_date)
        obs_orders = orders_merged[orders_merged["purchase_dt"] < cutoff_dt].copy()
        fut_orders = orders_merged[orders_merged["purchase_dt"] >= cutoff_dt].copy()

        # Observation customers: first purchase occurred before cutoff
        cust_first_dt = obs_orders.groupby("customer_unique_id")["purchase_dt"].min().reset_index().rename(columns={"purchase_dt": "first_purchase_dt"})
        cust_last_dt = obs_orders.groupby("customer_unique_id")["purchase_dt"].max().reset_index().rename(columns={"purchase_dt": "last_purchase_dt"})

        base_cust = obs_orders[["customer_unique_id", "customer_state", "customer_city"]].drop_duplicates(subset=["customer_unique_id"]).copy()
        base_cust = base_cust.merge(cust_first_dt, on="customer_unique_id", how="left")
        base_cust = base_cust.merge(cust_last_dt, on="customer_unique_id", how="left")

        # Compute observation features strictly prior to cutoff
        obs_orders["deliv_days"] = (obs_orders["deliv_dt"] - obs_orders["purchase_dt"]).dt.total_seconds() / 86400.0
        obs_orders["delay_days"] = (obs_orders["deliv_dt"] - obs_orders["estim_dt"]).dt.total_seconds() / 86400.0

        obs_profile = obs_orders.groupby("customer_unique_id").agg(
            obs_frequency_orders=("order_id", "nunique"),
            obs_monetary_value=("order_price", "sum"),
            obs_total_items=("items_qty", "sum"),
            obs_avg_freight=("order_freight", "mean"),
            obs_avg_delivery_days=("deliv_days", "mean"),
            obs_avg_delivery_delay=("delay_days", "mean"),
            late_count=("delay_days", lambda s: (s > 0).sum()),
            deliv_count=("deliv_dt", "count"),
        ).reset_index()

        base_cust = base_cust.merge(obs_profile, on="customer_unique_id", how="left")

        base_cust["customer_id"] = base_cust["customer_unique_id"]
        base_cust["first_purchase_date"] = base_cust["first_purchase_dt"].dt.strftime("%Y-%m-%d")
        base_cust["last_purchase_date"] = base_cust["last_purchase_dt"].dt.strftime("%Y-%m-%d")

        base_cust["obs_customer_age_days"] = ((cutoff_dt - base_cust["first_purchase_dt"]).dt.total_seconds() / 86400.0).round(2)
        base_cust["obs_recency_days"] = ((cutoff_dt - base_cust["last_purchase_dt"]).dt.total_seconds() / 86400.0).round(2)
        base_cust["obs_avg_order_value"] = np.where(
            base_cust["obs_frequency_orders"] > 0,
            (base_cust["obs_monetary_value"] / base_cust["obs_frequency_orders"]).round(2),
            0.0,
        )
        base_cust["obs_avg_items_per_order"] = np.where(
            base_cust["obs_frequency_orders"] > 0,
            (base_cust["obs_total_items"] / base_cust["obs_frequency_orders"]).round(2),
            0.0,
        )
        base_cust["obs_late_delivery_ratio"] = np.where(
            base_cust["deliv_count"] > 0,
            (base_cust["late_count"] / base_cust["deliv_count"]).round(4),
            0.0,
        )

        # Payment features before cutoff
        obs_pmts = payments_df.merge(obs_orders[["order_id", "customer_unique_id"]], on="order_id", how="inner")
        pmt_profile = obs_pmts.groupby("customer_unique_id").agg(
            obs_avg_installments=("payment_installments", "mean")
        ).reset_index()
        pref_pmt = (
            obs_pmts.groupby(["customer_unique_id", "payment_type"])["payment_sequential"]
            .count()
            .reset_index()
            .sort_values(by=["customer_unique_id", "payment_sequential"], ascending=[True, False])
            .drop_duplicates(subset=["customer_unique_id"])
            .rename(columns={"payment_type": "obs_preferred_payment"})
        )

        base_cust = base_cust.merge(pmt_profile, on="customer_unique_id", how="left")
        base_cust = base_cust.merge(pref_pmt[["customer_unique_id", "obs_preferred_payment"]], on="customer_unique_id", how="left")
        base_cust["obs_avg_installments"] = base_cust["obs_avg_installments"].fillna(1.0).round(2)
        base_cust["obs_preferred_payment"] = base_cust["obs_preferred_payment"].fillna("credit_card")

        # Review features before cutoff
        obs_revs = reviews_df.merge(obs_orders[["order_id", "customer_unique_id"]], on="order_id", how="inner")
        rev_profile = obs_revs.groupby("customer_unique_id").agg(
            obs_avg_review_score=("review_score", "mean"),
            obs_review_count=("review_id", "count"),
        ).reset_index()
        base_cust = base_cust.merge(rev_profile, on="customer_unique_id", how="left")
        base_cust["obs_avg_review_score"] = base_cust["obs_avg_review_score"].fillna(4.0).round(2)
        base_cust["obs_review_count"] = base_cust["obs_review_count"].fillna(0).astype(int)

        # Compute TARGET VARIABLES strictly from orders >= cutoff_date
        fut_rev_per_cust = fut_orders.groupby("customer_unique_id")["order_price"].sum().reset_index().rename(columns={"order_price": "target_future_clv"})
        base_cust = base_cust.merge(fut_rev_per_cust, on="customer_unique_id", how="left")
        base_cust["target_future_clv"] = base_cust["target_future_clv"].fillna(0.0).round(2)
        base_cust["target_repeat_buyer"] = (base_cust["target_future_clv"] > 0).astype(int)

        # Drop temporary counts
        base_cust = base_cust.drop(columns=["late_count", "deliv_count", "first_purchase_dt", "last_purchase_dt"], errors="ignore")

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Temporal Feature Store Engineering for {len(base_cust):,} observation customers in {elapsed_sec:.2f}s.")

        if output_dir:
            target_dir = Path(output_dir)
            target_dir.mkdir(parents=True, exist_ok=True)
            base_cust.to_parquet(target_dir / "temporal_feature_store.parquet", index=False)

        return base_cust

