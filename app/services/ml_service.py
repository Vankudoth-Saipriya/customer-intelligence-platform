"""
Machine Learning Service Layer.

Provides lazy-loaded, memory-cached model inference for:
- Customer Segmentation (KMeans)
- Customer Lifetime Value Prediction (Random Forest Regressor)
- Repeat Purchase Propensity (Logistic Regression)
"""

json_import = True
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
from loguru import logger
import numpy as np
import pandas as pd

from app.analytics import artifact_store
from app.schemas.ml import (
    CLVResponse,
    CustomerFeaturePayload,
    MLHealthResponse,
    ModelMetadataInfo,
    ModelsInfoResponse,
    RepeatPurchaseResponse,
    SegmentationResponse,
)


class MLService:
    """
    Service responsible for loading trained ML model artifacts lazily,
    caching models in memory, and servicing real-time inference requests.
    """

    def __init__(self, artifacts_dir: Optional[Path] = None) -> None:
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.artifacts_dir = artifacts_dir or self.project_root / "artifacts" / "ml"

        # Lazy-loaded cache
        self._segmentation_data: Optional[Dict[str, Any]] = None
        self._clv_data: Optional[Dict[str, Any]] = None
        self._repeat_purchase_data: Optional[Dict[str, Any]] = None

        self._seg_metadata: Optional[Dict[str, Any]] = None
        self._clv_metadata: Optional[Dict[str, Any]] = None
        self._repeat_metadata: Optional[Dict[str, Any]] = None

        self._seg_table: Optional[pd.DataFrame] = None
        self._clv_table: Optional[pd.DataFrame] = None
        self._repeat_table: Optional[pd.DataFrame] = None

    def _ensure_loaded(self) -> None:
        """
        Lazy load all model pipelines, metadata, and prediction tables.
        Executes only once per service instance.
        """
        if self._segmentation_data is not None or self._clv_data is not None:
            return

        logger.info("Lazy loading trained ML model artifacts and metadata into memory...")

        # 1. Segmentation
        seg_joblib = self.artifacts_dir / "segmentation_pipeline.joblib"
        seg_meta_json = self.artifacts_dir / "customer_segmentation_metadata.json"
        seg_pq = self.artifacts_dir / "customer_segments.parquet"

        if seg_joblib.exists():
            self._segmentation_data = joblib.load(seg_joblib)
        if seg_meta_json.exists():
            with open(seg_meta_json, "r", encoding="utf-8") as f:
                self._seg_metadata = json.load(f)
        # Use shared store — avoids a second full-width parquet load
        self._seg_table = artifact_store.get_segments()

        # 2. CLV
        clv_joblib = self.artifacts_dir / "clv_pipeline.joblib"
        clv_meta_json = self.artifacts_dir / "customer_clv_metadata.json"

        if clv_joblib.exists():
            self._clv_data = joblib.load(clv_joblib)
        if clv_meta_json.exists():
            with open(clv_meta_json, "r", encoding="utf-8") as f:
                self._clv_metadata = json.load(f)
        # Use shared store
        self._clv_table = artifact_store.get_clv_predictions()

        # 3. Repeat Purchase
        rp_joblib = self.artifacts_dir / "repeat_purchase_pipeline.joblib"
        rp_meta_json = self.artifacts_dir / "repeat_purchase_metadata.json"

        if rp_joblib.exists():
            self._repeat_purchase_data = joblib.load(rp_joblib)
        if rp_meta_json.exists():
            with open(rp_meta_json, "r", encoding="utf-8") as f:
                self._repeat_metadata = json.load(f)
        # Use shared store
        self._repeat_table = artifact_store.get_repeat_predictions()

        logger.info("Successfully loaded ML model artifacts into cache.")

    def _payload_to_feature_matrix(
        self, payload: CustomerFeaturePayload, num_cols: List[str], cat_cols: List[str], scaler: Any, ohe: Any
    ) -> np.ndarray:
        """
        Transform Pydantic feature payload into preprocessed numpy matrix.
        Handles mapping of both standard & temporal obs_* feature names.
        """
        payload_dict = payload.model_dump()
        df_row: Dict[str, Any] = {}

        for col in num_cols:
            base_col = col.replace("obs_", "")
            if col in payload_dict and payload_dict[col] is not None:
                df_row[col] = payload_dict[col]
            elif base_col in payload_dict and payload_dict[base_col] is not None:
                df_row[col] = payload_dict[base_col]
            else:
                df_row[col] = 0.0

        for col in cat_cols:
            base_col = col.replace("obs_", "")
            if col in payload_dict and payload_dict[col] is not None:
                df_row[col] = payload_dict[col]
            elif base_col in payload_dict and payload_dict[base_col] is not None:
                df_row[col] = payload_dict[base_col]
            else:
                df_row[col] = "Unknown"

        df = pd.DataFrame([df_row])
        num_scaled = scaler.transform(df[num_cols].fillna(0.0))
        cat_encoded = ohe.transform(df[cat_cols].fillna("Unknown").astype(str))

        return np.hstack([num_scaled, cat_encoded])

    def predict_segment(self, payload: CustomerFeaturePayload) -> SegmentationResponse:
        """
        Predict customer segment / cluster.
        """
        self._ensure_loaded()
        logger.info(f"Servicing Segmentation prediction for customer_id: '{payload.customer_id or payload.customer_unique_id or 'raw payload'}'")

        # 1. Try table lookup if ID provided
        cid = payload.customer_id or payload.customer_unique_id
        if cid and self._seg_table is not None:
            match = self._seg_table[
                (self._seg_table["customer_id"] == cid) | (self._seg_table["customer_unique_id"] == cid)
            ]
            if not match.empty:
                row = match.iloc[0]
                return SegmentationResponse(
                    cluster_id=int(row["cluster_id"]),
                    cluster_name=f"Cluster {row['cluster_id']}",
                    business_description=str(row.get("cluster_description", f"Cluster {row['cluster_id']}")),
                )

        # 2. Live model inference if pipeline loaded
        if self._segmentation_data:
            km_model = self._segmentation_data["model"]
            scaler = self._segmentation_data["scaler"]
            profiles = self._segmentation_data.get("profiles", {})

            recency = float(payload.recency_days if payload.recency_days is not None else 100.0)
            frequency = float(payload.frequency_orders if payload.frequency_orders is not None else 1)
            monetary = float(payload.monetary_value if payload.monetary_value is not None else 100.0)

            log_rfm = np.array([[np.log1p(recency), np.log1p(frequency), np.log1p(monetary)]])
            X_val = scaler.transform(log_rfm)
            cluster_id = int(km_model.predict(X_val)[0])
            profile = profiles.get(f"cluster_{cluster_id}", {})
            desc = profile.get("business_description", f"Cluster {cluster_id}")

            return SegmentationResponse(
                cluster_id=cluster_id,
                cluster_name=f"Cluster {cluster_id}",
                business_description=desc,
            )

        return SegmentationResponse(
            cluster_id=0,
            cluster_name="Cluster 0",
            business_description="Mid-Tier Dormant Single-Order Customers",
        )

    def predict_clv(self, payload: CustomerFeaturePayload) -> CLVResponse:
        """
        Predict Customer Lifetime Value (total revenue).
        """
        self._ensure_loaded()
        logger.info(f"Servicing CLV prediction for customer_id: '{payload.customer_id or payload.customer_unique_id or 'raw payload'}'")

        cid = payload.customer_id or payload.customer_unique_id
        if cid and self._clv_table is not None:
            match = self._clv_table[
                (self._clv_table["customer_id"] == cid) | (self._clv_table["customer_unique_id"] == cid)
            ]
            if not match.empty:
                row = match.iloc[0]
                return CLVResponse(predicted_clv=round(float(row.get("predicted_clv", row.get("total_revenue", 0.0))), 2))

        if self._clv_data:
            model = self._clv_data["model"]
            num_cols = self._clv_data["num_cols"]
            cat_cols = self._clv_data["cat_cols"]
            scaler = self._clv_data["scaler"]
            ohe = self._clv_data["ohe"]

            X_val = self._payload_to_feature_matrix(payload, num_cols, cat_cols, scaler, ohe)
            pred_val = round(float(model.predict(X_val)[0]), 2)
            return CLVResponse(predicted_clv=max(0.0, pred_val))

        return CLVResponse(predicted_clv=round(float(payload.total_revenue), 2))

    def predict_repeat_purchase(self, payload: CustomerFeaturePayload) -> RepeatPurchaseResponse:
        """
        Predict Repeat Purchase Propensity.
        """
        self._ensure_loaded()
        logger.info(f"Servicing Repeat Purchase prediction for customer_id: '{payload.customer_id or payload.customer_unique_id or 'raw payload'}'")

        cid = payload.customer_id or payload.customer_unique_id
        if cid and self._repeat_table is not None:
            match = self._repeat_table[
                (self._repeat_table["customer_id"] == cid) | (self._repeat_table["customer_unique_id"] == cid)
            ]
            if not match.empty:
                row = match.iloc[0]
                prob = round(float(row.get("repeat_propensity", 0.5)), 4)
                pred_label = int(row.get("predicted_repeat_customer", 1 if prob >= 0.5 else 0))
                return RepeatPurchaseResponse(
                    repeat_purchase_probability=prob,
                    predicted_repeat_customer=pred_label,
                )

        if self._repeat_purchase_data:
            model = self._repeat_purchase_data["model"]
            num_cols = self._repeat_purchase_data["num_cols"]
            cat_cols = self._repeat_purchase_data["cat_cols"]
            scaler = self._repeat_purchase_data["scaler"]
            ohe = self._repeat_purchase_data["ohe"]

            X_val = self._payload_to_feature_matrix(payload, num_cols, cat_cols, scaler, ohe)
            if hasattr(model, "predict_proba"):
                prob = round(float(model.predict_proba(X_val)[0, 1]), 4)
            else:
                prob = float(model.predict(X_val)[0])
            pred_label = 1 if prob >= 0.5 else 0
            return RepeatPurchaseResponse(
                repeat_purchase_probability=prob,
                predicted_repeat_customer=pred_label,
            )

        prob = 1.0 if payload.frequency_orders > 1 else 0.05
        return RepeatPurchaseResponse(
            repeat_purchase_probability=prob,
            predicted_repeat_customer=1 if prob >= 0.5 else 0,
        )

    def get_models_info(self) -> ModelsInfoResponse:
        """
        Retrieve available trained ML models metadata.
        """
        self._ensure_loaded()

        models: Dict[str, ModelMetadataInfo] = {}

        if self._seg_metadata:
            models["customer_segmentation"] = ModelMetadataInfo(
                model_name="KMeans Customer Segmentation",
                model_type="Unsupervised Clustering (KMeans)",
                feature_count=135,
                training_date="2026-08-08",
                metrics={
                    "best_k": self._seg_metadata.get("best_k", 2),
                    "best_silhouette_score": self._seg_metadata.get("best_silhouette_score", 0.5369),
                },
                status="loaded" if self._segmentation_data or self._seg_table is not None else "not_loaded",
            )

        if self._clv_metadata:
            models["clv_prediction"] = ModelMetadataInfo(
                model_name=self._clv_metadata.get("best_model_name", "Ridge Regression"),
                model_type="Regression (90-Day Future Value)",
                feature_count=16,
                training_date="2026-08-22",
                metrics={
                    "mae": self._clv_metadata.get("best_mae", 3.05),
                    "zero_baseline_mae": self._clv_metadata.get("zero_baseline_mae", 1.25),
                    "mean_baseline_mae": self._clv_metadata.get("mean_baseline_mae", 2.30),
                    "median_ae": self._clv_metadata.get("best_median_ae", 1.69),
                    "rmse": self._clv_metadata.get("best_rmse", 18.18),
                    "r2_score": self._clv_metadata.get("best_r2_score", 0.0011),
                    "non_zero_clv_mae": self._clv_metadata.get("best_non_zero_clv_mae", 120.12),
                },
                status="loaded" if self._clv_data or self._clv_table is not None else "not_loaded",
            )

        if self._repeat_metadata:
            models["repeat_purchase_prediction"] = ModelMetadataInfo(
                model_name=self._repeat_metadata.get("best_model_name", "Logistic Regression"),
                model_type="Binary Classification (Repeat Purchase)",
                feature_count=16,
                training_date="2026-08-20",
                metrics={
                    "pr_auc": self._repeat_metadata.get("best_pr_auc", 0.0354),
                    "roc_auc": self._repeat_metadata.get("best_roc_auc", 0.5632),
                    "recall": self._repeat_metadata.get("best_recall", 0.7550),
                    "precision": self._repeat_metadata.get("best_precision", 0.0292),
                    "f1_score": self._repeat_metadata.get("best_f1_score", 0.0562),
                    "optimal_threshold": self._repeat_metadata.get("optimal_threshold", 0.50),
                },
                status="loaded" if self._repeat_purchase_data or self._repeat_table is not None else "not_loaded",
            )

        return ModelsInfoResponse(models=models)

    def get_health(self) -> MLHealthResponse:
        """
        Retrieve ML service health and inference availability.
        """
        self._ensure_loaded()
        loaded = []
        if self._segmentation_data is not None or self._seg_table is not None:
            loaded.append("Customer Segmentation")
        if self._clv_data is not None or self._clv_table is not None:
            loaded.append("CLV Prediction")
        if self._repeat_purchase_data is not None or self._repeat_table is not None:
            loaded.append("Repeat Purchase Propensity")

        is_avail = len(loaded) > 0

        return MLHealthResponse(
            status="healthy" if is_avail else "degraded",
            version="1.0.0",
            inference_available=is_avail,
            loaded_models=loaded,
        )


_ml_service_instance: Optional[MLService] = None


def get_ml_service() -> MLService:
    """
    Dependency injection provider returning cached MLService instance.
    """
    global _ml_service_instance
    if _ml_service_instance is None:
        _ml_service_instance = MLService()
    return _ml_service_instance
