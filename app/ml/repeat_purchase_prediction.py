"""
Repeat Purchase Propensity Prediction ML Module.

Trains and evaluates classification models to predict whether a customer will become a repeat buyer:
- Target: repeat_customer (1 if frequency_orders > 1 else 0)
- Classifiers: Logistic Regression, Random Forest Classifier, Gradient Boosting Classifier
- Data Split: 80/20 train/test split (random_state=42, stratify=y)
- Evaluates Accuracy, Precision, Recall, F1 Score, ROC-AUC, and Confusion Matrix
- Selects best model based on ROC-AUC
- Computes Top 20 Feature Importances
- Exports Parquet, CSV predictions and JSON metadata artifacts
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.report import RepeatPurchasePredictionReport


class RepeatPurchasePredictor:
    """
    ML Pipeline for predicting Customer Repeat Purchase Propensity.
    """

    def __init__(
        self,
        feature_store_path: Optional[Path] = None,
        random_state: int = 42,
    ) -> None:
        """
        Initialize RepeatPurchasePredictor pipeline.
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

    def preprocess(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str], pd.DataFrame]:
        """
        Preprocess feature table for classification modeling:
        - Target definition: repeat_customer = (frequency_orders > 1).astype(int)
        - Exclude identifiers & target leakage columns
        - One-hot encode categoricals, standard scale numerics
        - Train/Test Split (80/20, random_state=42, stratify)
        """
        logger.info("Preprocessing features for Repeat Purchase Propensity (removing leakage, OHE, Scaling, 80/20 split)...")

        # Define target variable
        df["repeat_customer"] = (df["frequency_orders"] > 1).astype(int)
        y = df["repeat_customer"].values

        # Identifiers & Target Leakage columns to drop
        exclude_cols = [
            "customer_id",
            "customer_unique_id",
            "first_purchase_date",
            "last_purchase_date",
            "city",
            "repeat_customer",
            "frequency_orders",
            "repeat_purchase_rate",
            "days_between_orders_mean",
            "order_value_std",
            "order_frequency_per_month",
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

        X = np.hstack([num_scaled, cat_encoded])
        feature_names = num_cols + encoded_cat_feature_names

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=self.random_state, stratify=y
        )

        logger.info(f"Split dataset into Train: {len(X_train):,} rows, Test: {len(X_test):,} rows across {X.shape[1]} features.")
        return X_train, X_test, y_train, y_test, feature_names, df

    def train_and_evaluate(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
    ) -> Tuple[Dict[str, Dict[str, Any]], str, Any, float]:
        """
        Train and compare Logistic Regression, Random Forest, and Gradient Boosting classifiers.
        Selects best model based on highest test ROC-AUC score.
        """
        logger.info("Training and evaluating classification models with class balancing...")
        t0 = time.perf_counter()

        models = {
            "Logistic Regression": LogisticRegression(
                class_weight="balanced", random_state=self.random_state, max_iter=1000
            ),
            "Random Forest Classifier": RandomForestClassifier(
                n_estimators=100, max_depth=12, class_weight="balanced", random_state=self.random_state, n_jobs=-1
            ),
            "Gradient Boosting Classifier": GradientBoostingClassifier(
                n_estimators=50, max_depth=4, random_state=self.random_state
            ),
        }

        comparison: Dict[str, Dict[str, Any]] = {}
        best_model_name = ""
        best_roc_auc = -float("inf")
        best_model = None

        for name, model in models.items():
            m_t0 = time.perf_counter()
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            probs = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else preds
            m_t_elapsed = time.perf_counter() - m_t0

            acc = round(float(accuracy_score(y_test, preds)), 4)
            prec = round(float(precision_score(y_test, preds, zero_division=0)), 4)
            rec = round(float(recall_score(y_test, preds, zero_division=0)), 4)
            f1 = round(float(f1_score(y_test, preds, zero_division=0)), 4)
            roc_auc = round(float(roc_auc_score(y_test, probs)), 4)
            cm = confusion_matrix(y_test, preds).tolist()

            comparison[name] = {
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
                "roc_auc": roc_auc,
                "confusion_matrix": cm,
                "train_time_sec": round(m_t_elapsed, 4),
            }

            logger.info(f"Model '{name}' -> ROC-AUC: {roc_auc:.4f} | F1: {f1:.4f} | Accuracy: {acc:.4f} ({m_t_elapsed:.2f}s)")

            if roc_auc > best_roc_auc:
                best_roc_auc = roc_auc
                best_model_name = name
                best_model = model

        total_training_time = time.perf_counter() - t0
        logger.info(f"Best performing classification model selected by ROC-AUC: '{best_model_name}' (ROC-AUC: {best_roc_auc:.4f}).")

        return comparison, best_model_name, best_model, total_training_time

    def extract_feature_importance(
        self, model: Any, feature_names: List[str], top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Extract top N feature importances or coefficient absolute weights from the selected model.
        """
        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            importances = np.abs(model.coef_[0])
        else:
            importances = np.zeros(len(feature_names))

        feat_imp_df = (
            pd.DataFrame({"feature": feature_names, "importance": importances})
            .sort_values(by="importance", ascending=False)
            .head(top_n)
        )

        top_features = [
            {"feature": row["feature"], "importance_score": round(float(row["importance"]), 6)}
            for _, row in feat_imp_df.iterrows()
        ]
        return top_features

    def run(self, output_dir: Optional[Path] = None) -> RepeatPurchasePredictionReport:
        """
        Run full Repeat Purchase Propensity pipeline:
        Load -> Preprocess -> Train & Evaluate -> Extract Importances -> Predict -> Export Artifacts.
        """
        start_time = time.perf_counter()
        logger.info("Executing Repeat Purchase Propensity Prediction Pipeline...")

        # 1. Load Data
        df = self.load_data()
        total_customers = len(df)

        # 2. Preprocess
        X_train, X_test, y_train, y_test, feature_names, full_df = self.preprocess(df)

        class_dist = {
            "non_repeat_customers": int((full_df["repeat_customer"] == 0).sum()),
            "repeat_customers": int((full_df["repeat_customer"] == 1).sum()),
        }

        # Re-create full X feature matrix for inference across all 96k customers
        cat_cols = ["state", "favorite_product_category", "preferred_payment_method", "customer_value_tier"]
        exclude_cols = [
            "customer_id", "customer_unique_id", "first_purchase_date", "last_purchase_date",
            "city", "repeat_customer", "frequency_orders", "repeat_purchase_rate",
            "days_between_orders_mean", "order_value_std", "order_frequency_per_month"
        ]
        feature_cols = [c for c in full_df.columns if c not in exclude_cols]
        num_cols = [c for c in feature_cols if c not in cat_cols]

        scaler = StandardScaler().fit(full_df[num_cols].fillna(0.0))
        num_scaled_full = scaler.transform(full_df[num_cols].fillna(0.0))

        ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit(full_df[cat_cols].fillna("Unknown").astype(str))
        cat_encoded_full = ohe.transform(full_df[cat_cols].fillna("Unknown").astype(str))

        X_full = np.hstack([num_scaled_full, cat_encoded_full])

        # 3. Train & Compare Models
        comparison, best_model_name, best_model, training_time = self.train_and_evaluate(
            X_train, X_test, y_train, y_test
        )

        # 4. Extract Top 20 Feature Importances
        top_importances = self.extract_feature_importance(best_model, feature_names, top_n=20)

        # 5. Predict across complete customer dataset
        t_pred_start = time.perf_counter()
        if hasattr(best_model, "predict_proba"):
            full_df["repeat_propensity"] = best_model.predict_proba(X_full)[:, 1].round(4)
        else:
            full_df["repeat_propensity"] = best_model.predict(X_full).astype(float)

        full_df["predicted_repeat_customer"] = (full_df["repeat_propensity"] >= 0.5).astype(int)
        pred_time = time.perf_counter() - t_pred_start

        best_metrics = comparison[best_model_name]

        # 6. Export Artifacts
        if output_dir is None:
            target_dir = self.project_root / "artifacts" / "ml"
        else:
            target_dir = Path(output_dir)

        target_dir.mkdir(parents=True, exist_ok=True)

        csv_path = target_dir / "repeat_purchase_predictions.csv"
        parquet_path = target_dir / "repeat_purchase_predictions.parquet"
        joblib_path = target_dir / "repeat_purchase_pipeline.joblib"

        import joblib
        joblib.dump(
            {
                "model": best_model,
                "model_name": best_model_name,
                "feature_names": feature_names,
                "scaler": scaler,
                "ohe": ohe,
                "num_cols": num_cols,
                "cat_cols": cat_cols,
            },
            joblib_path,
        )
        logger.info(f"Exported joblib repeat purchase pipeline -> '{joblib_path.resolve()}'")

        logger.info(f"Exporting CSV repeat purchase predictions artifact -> '{csv_path.resolve()}'")
        full_df.to_csv(csv_path, index=False)

        logger.info(f"Exporting Parquet repeat purchase predictions artifact -> '{parquet_path.resolve()}'")
        full_df.to_parquet(parquet_path, index=False, engine="pyarrow")

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Repeat Purchase Propensity Pipeline in {elapsed_sec:.4f}s.")

        report = RepeatPurchasePredictionReport(
            total_customers=total_customers,
            class_distribution=class_dist,
            best_model_name=best_model_name,
            best_roc_auc=best_metrics["roc_auc"],
            best_f1_score=best_metrics["f1_score"],
            best_accuracy=best_metrics["accuracy"],
            best_precision=best_metrics["precision"],
            best_recall=best_metrics["recall"],
            model_comparison=comparison,
            feature_importance=top_importances,
            csv_path=str(csv_path.resolve()),
            parquet_path=str(parquet_path.resolve()),
            metadata_path="",
            training_time_sec=round(training_time, 4),
            prediction_time_sec=round(pred_time, 4),
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save metadata report to artifacts/ml/repeat_purchase_metadata.json
        report.save_json()

        return report
