"""
Customer Segmentation ML Module.

Performs KMeans clustering over the Customer Feature Store:
1. Data Preparation (imputation, OHE, standard scaling, ID preservation)
2. Model Selection (evaluates k=2 to 10 for Silhouette, Davies-Bouldin, Calinski-Harabasz, Inertia)
3. Model Training (fits final KMeans with optimal k, random_state=42)
4. Cluster Analysis & Business Description Generation
5. Exports Parquet, CSV, and JSON metadata artifacts
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.report import CustomerSegmentationReport


class CustomerSegmentation:
    """
    ML Pipeline executing unsupervised customer segmentation using KMeans.
    """

    def __init__(
        self,
        feature_store_path: Optional[Path] = None,
        random_state: int = 42,
    ) -> None:
        """
        Initialize CustomerSegmentation pipeline.
        """
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.feature_store_path = (
            Path(feature_store_path)
            if feature_store_path
            else self.project_root / "artifacts" / "features" / "customer_feature_store.parquet"
        )
        self.random_state = random_state

    def load_data(self) -> pd.DataFrame:
        """
        Load Customer Feature Store DataFrame.
        """
        logger.info(f"Loading Customer Feature Store from: '{self.feature_store_path}'")
        if not self.feature_store_path.exists():
            raise FileNotFoundError(f"Feature store artifact not found at: {self.feature_store_path}")
        df = pd.read_parquet(self.feature_store_path)
        logger.info(f"Loaded Feature Store dataset ({len(df):,} rows, {len(df.columns)} columns).")
        return df

    def preprocess(self, df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Preprocess feature table for training:
        - Exclude identifier & date columns
        - One-hot encode categorical features
        - Standardize numerical features
        """
        logger.info("Preprocessing features (imputation, OHE, standard scaling)...")

        exclude_cols = [
            "customer_id",
            "customer_unique_id",
            "first_purchase_date",
            "last_purchase_date",
            "city",
        ]

        feature_cols = [c for c in df.columns if c not in exclude_cols]

        cat_cols = ["state", "favorite_product_category", "preferred_payment_method", "customer_value_tier"]
        num_cols = [c for c in feature_cols if c not in cat_cols]

        # Handle numerical scaling
        num_df = df[num_cols].fillna(0.0)
        scaler = StandardScaler()
        num_scaled = scaler.fit_transform(num_df)

        # Handle categorical encoding
        cat_df = df[cat_cols].fillna("Unknown").astype(str)
        ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        cat_encoded = ohe.fit_transform(cat_df)
        encoded_cat_feature_names = list(ohe.get_feature_names_out(cat_cols))

        X_prep = np.hstack([num_scaled, cat_encoded])
        feature_names = num_cols + encoded_cat_feature_names

        logger.info(f"Feature matrix preprocessed: shape {X_prep.shape}.")
        return X_prep, feature_names

    def evaluate_k(
        self, X_prep: np.ndarray, min_k: int = 2, max_k: int = 10
    ) -> Tuple[Dict[str, Dict[str, float]], int]:
        """
        Evaluate KMeans models for k in [min_k, max_k].
        Computes Silhouette Score, Davies-Bouldin Index, Calinski-Harabasz Score, Inertia.
        Returns evaluation dict and optimal k selected by maximum Silhouette Score.
        """
        logger.info(f"Evaluating KMeans clustering for k = {min_k} to {max_k}...")

        metrics: Dict[str, Dict[str, float]] = {}
        best_k = min_k
        best_sil = -1.0

        np.random.seed(self.random_state)
        subsample_size = min(10000, len(X_prep))
        subsample_idx = np.random.choice(len(X_prep), size=subsample_size, replace=False)
        X_sub = X_prep[subsample_idx]

        for k in range(min_k, max_k + 1):
            km = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            labels = km.fit_predict(X_prep)
            labels_sub = labels[subsample_idx]

            sil_score = round(float(silhouette_score(X_sub, labels_sub)), 4)
            db_index = round(float(davies_bouldin_score(X_prep, labels)), 4)
            ch_score = round(float(calinski_harabasz_score(X_prep, labels)), 2)
            inertia = round(float(km.inertia_), 2)

            metrics[f"k_{k}"] = {
                "k": k,
                "silhouette_score": sil_score,
                "davies_bouldin_index": db_index,
                "calinski_harabasz_score": ch_score,
                "inertia": inertia,
            }

            logger.info(f"k={k} | Silhouette: {sil_score:.4f} | Davies-Bouldin: {db_index:.4f} | Calinski-Harabasz: {ch_score:,.2f} | Inertia: {inertia:,.2f}")

            if sil_score > best_sil:
                best_sil = sil_score
                best_k = k

        logger.info(f"Optimal cluster count selected by Silhouette Score: k={best_k} (Score: {best_sil:.4f}).")
        return metrics, best_k

    def generate_business_description(self, profile: Dict[str, Any], pop_medians: Dict[str, float]) -> str:
        """
        Rule-based automatic business description generator for a cluster.
        No LLM used - deterministic, domain-grounded profiling.
        """
        avg_rev = profile["average_revenue"]
        avg_orders = profile["average_orders"]
        avg_review = profile["average_review_score"]
        avg_recency = profile["average_recency"]
        tier = profile["dominant_customer_value_tier"]

        prefix = ""
        if avg_rev >= pop_medians.get("q75_revenue", 200.0) or tier == "High Value":
            prefix = "High-Value"
        elif avg_rev <= pop_medians.get("q25_revenue", 60.0) or tier == "Low Value":
            prefix = "Low-Spending"
        else:
            prefix = "Mid-Tier"

        freq_label = ""
        if avg_orders > 1.5:
            freq_label = "Loyal Repeat Buyers"
        elif avg_recency < pop_medians.get("median_recency", 200.0):
            freq_label = "Recent Occasional Buyers"
        else:
            freq_label = "Dormant Single-Order Customers"

        quality_suffix = ""
        if avg_review >= 4.3:
            quality_suffix = " (Highly Satisfied)"
        elif avg_review <= 3.5:
            quality_suffix = " (Low Rating Risk)"

        return f"{prefix} {freq_label}{quality_suffix}"

    def analyze_clusters(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        Perform cluster profiling across customer segments and generate business descriptions.
        """
        logger.info("Performing cluster analysis and generating business descriptions...")

        pop_medians = {
            "q75_revenue": float(df["total_revenue"].quantile(0.75)),
            "q25_revenue": float(df["total_revenue"].quantile(0.25)),
            "median_recency": float(df["recency_days"].median()),
        }

        cluster_profiles: Dict[str, Dict[str, Any]] = {}
        unique_clusters = sorted(df["cluster_id"].unique())

        for c_id in unique_clusters:
            c_df = df[df["cluster_id"] == c_id]

            c_count = len(c_df)
            avg_rev = round(float(c_df["total_revenue"].mean()), 2)
            avg_orders = round(float(c_df["frequency_orders"].mean()), 2)
            avg_review = round(float(c_df["avg_review_score"].mean()), 2)
            avg_delay = round(float(c_df["avg_delivery_delay"].mean()), 2)
            avg_aov = round(float(c_df["avg_order_value"].mean()), 2)
            avg_recency = round(float(c_df["recency_days"].mean()), 2)
            avg_frequency = avg_orders
            avg_monetary = avg_rev

            pref_pmt = c_df["preferred_payment_method"].mode().iloc[0] if not c_df["preferred_payment_method"].empty else "Unknown"
            dom_tier = c_df["customer_value_tier"].mode().iloc[0] if not c_df["customer_value_tier"].empty else "Low Value"

            profile = {
                "cluster_id": int(c_id),
                "customer_count": c_count,
                "customer_percentage": round((c_count / len(df) * 100.0), 2),
                "average_revenue": avg_rev,
                "average_orders": avg_orders,
                "average_review_score": avg_review,
                "average_delivery_delay": avg_delay,
                "average_order_value": avg_aov,
                "average_recency": avg_recency,
                "average_frequency": avg_frequency,
                "average_monetary_value": avg_monetary,
                "preferred_payment_method": str(pref_pmt),
                "dominant_customer_value_tier": str(dom_tier),
            }

            desc = self.generate_business_description(profile, pop_medians)
            profile["business_description"] = desc
            cluster_profiles[f"cluster_{c_id}"] = profile

        return cluster_profiles

    def run(self, output_dir: Optional[Path] = None) -> CustomerSegmentationReport:
        """
        Run full segmentation pipeline:
        Load -> Preprocess -> Evaluate -> Fit Best Model -> Analyze -> Export Artifacts.
        """
        start_time = time.perf_counter()
        logger.info("Executing Customer Segmentation ML Pipeline...")

        # 1. Load Data
        df = self.load_data()
        total_customers = len(df)

        # 2. Preprocess
        X_prep, feature_names = self.preprocess(df)

        # 3. Model Selection
        eval_metrics, best_k = self.evaluate_k(X_prep, min_k=2, max_k=10)
        best_sil_score = eval_metrics[f"k_{best_k}"]["silhouette_score"]

        # 4. Model Training & Cluster Assignment
        logger.info(f"Training final KMeans model with best_k={best_k}...")
        final_km = KMeans(n_clusters=best_k, random_state=self.random_state, n_init=10)
        df["cluster_id"] = final_km.fit_predict(X_prep)

        # 5. Cluster Analysis
        profiles = self.analyze_clusters(df)

        # Map business descriptions to dataframe
        desc_map = {int(p["cluster_id"]): p["business_description"] for p in profiles.values()}
        df["cluster_description"] = df["cluster_id"].map(desc_map)

        # 6. Export Artifacts
        if output_dir is None:
            target_dir = self.project_root / "artifacts" / "ml"
        else:
            target_dir = Path(output_dir)

        target_dir.mkdir(parents=True, exist_ok=True)

        csv_path = target_dir / "customer_segments.csv"
        parquet_path = target_dir / "customer_segments.parquet"
        joblib_path = target_dir / "segmentation_pipeline.joblib"

        import joblib
        joblib.dump(
            {
                "model": final_km,
                "feature_names": feature_names,
                "profiles": profiles,
            },
            joblib_path,
        )
        logger.info(f"Exported joblib segmentation pipeline -> '{joblib_path.resolve()}'")

        logger.info(f"Exporting CSV segments artifact -> '{csv_path.resolve()}'")
        df.to_csv(csv_path, index=False)

        logger.info(f"Exporting Parquet segments artifact -> '{parquet_path.resolve()}'")
        df.to_parquet(parquet_path, index=False, engine="pyarrow")

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Customer Segmentation Pipeline in {elapsed_sec:.4f}s.")

        report = CustomerSegmentationReport(
            total_customers_segmented=total_customers,
            best_k=best_k,
            best_silhouette_score=best_sil_score,
            model_evaluation_metrics=eval_metrics,
            cluster_profiles=profiles,
            csv_path=str(csv_path.resolve()),
            parquet_path=str(parquet_path.resolve()),
            metadata_path="",
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save metadata report to artifacts/ml/customer_segmentation_metadata.json
        report.save_json()

        return report
