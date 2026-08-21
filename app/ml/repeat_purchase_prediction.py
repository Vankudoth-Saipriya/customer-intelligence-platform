"""
Repeat Purchase Propensity Prediction ML Module.

Trains and evaluates leakage-free temporal classification models to predict repeat buyer likelihood:
- Cutoff Date: 2017-10-01
- Target: target_repeat_buyer (1 if customer placed at least 1 order between 2017-10-01 and 2018-10-17, else 0)
- Predictors: Engineered strictly from orders placed BEFORE 2017-10-01
- Split: Chronological Train/Test split (Train: acquisition < 2017-06-01, Test: >= 2017-06-01 and < 2017-10-01)
- Classifiers: Logistic Regression (balanced), Random Forest (balanced), Gradient Boosting Classifier, XGBoost Classifier (scale_pos_weight)
- Metrics: ROC-AUC, PR-AUC, Precision, Recall, F1 Score, Confusion Matrix, Class Distribution
- Exports Parquet, CSV predictions and JSON metadata artifacts
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.features.customer_feature_store import CustomerFeatureStore
from app.ml.report import RepeatPurchasePredictionReport


class RepeatPurchasePredictor:
    """
    ML Pipeline for predicting Customer Repeat Purchase Propensity.
    """

    def __init__(
        self,
        cutoff_date: str = "2017-10-01",
        random_state: int = 42,
    ) -> None:
        """
        Initialize RepeatPurchasePredictor pipeline.
        """
        self.project_root = Path(__file__).resolve().parent.parent.parent
        self.cutoff_date = cutoff_date
        self.random_state = random_state

    def load_data(self) -> pd.DataFrame:
        """
        Load or build Temporal Customer Feature Store DataFrame.
        """
        logger.info(f"Generating Temporal Customer Feature Store with Cutoff Date: '{self.cutoff_date}'...")
        fs = CustomerFeatureStore()
        df = fs.build_temporal_feature_store(cutoff_date=self.cutoff_date)
        df.columns = [str(c) for c in df.columns]
        logger.info(f"Loaded Temporal Feature Store dataset ({len(df):,} observation customers, {len(df.columns)} columns).")
        return df

    def preprocess(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[str], pd.DataFrame]:
        """
        Preprocess temporal feature table for classification modeling:
        - Target: target_repeat_buyer
        - Chronological Train/Test Split:
            - Train: first_purchase_date < 2017-06-01
            - Test: first_purchase_date >= 2017-06-01 and < 2017-10-01
        """
        logger.info("Preprocessing features for Repeat Purchase Propensity (chronological split, OHE, Scaling)...")

        df = df.copy()
        df.columns = [str(c) for c in df.columns]

        target_col = "target_repeat_buyer"
        if target_col not in df.columns:
            raise KeyError(f"Target column '{target_col}' missing from feature store!")

        num_cols = [
            "obs_recency_days", "obs_frequency_orders", "obs_monetary_value", "obs_avg_order_value",
            "obs_customer_age_days", "obs_total_items", "obs_avg_items_per_order", "obs_avg_freight",
            "obs_avg_delivery_days", "obs_avg_delivery_delay", "obs_late_delivery_ratio",
            "obs_avg_installments", "obs_avg_review_score", "obs_review_count"
        ]
        cat_cols = ["customer_state", "obs_preferred_payment"]

        # Chronological Train/Test Split
        split_dt = "2017-06-01"
        train_mask = df["first_purchase_date"] < split_dt
        test_mask = df["first_purchase_date"] >= split_dt

        train_df = df[train_mask].copy()
        test_df = df[test_mask].copy()

        # Handle numerical scaling
        scaler = StandardScaler()
        num_scaled_train = scaler.fit_transform(train_df[num_cols].fillna(0.0).values)
        num_scaled_test = scaler.transform(test_df[num_cols].fillna(0.0).values)

        # Handle categorical encoding
        ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
        cat_encoded_train = ohe.fit_transform(train_df[cat_cols].fillna("Unknown").values.astype(str))
        cat_encoded_test = ohe.transform(test_df[cat_cols].fillna("Unknown").values.astype(str))

        encoded_cat_feature_names = list(ohe.get_feature_names_out(cat_cols))

        X_train = np.hstack([num_scaled_train, cat_encoded_train])
        X_test = np.hstack([num_scaled_test, cat_encoded_test])

        y_train = train_df[target_col].values.astype(int)
        y_test = test_df[target_col].values.astype(int)

        feature_names = num_cols + encoded_cat_feature_names

        logger.info(f"Chronological Split -> Train: {len(X_train):,} rows (< {split_dt}), Test: {len(X_test):,} rows (>= {split_dt}) across {X_train.shape[1]} features.")
        return X_train, X_test, y_train, y_test, feature_names, df

    def train_and_evaluate(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
    ) -> Tuple[Dict[str, Dict[str, Any]], str, Any, float]:
        """
        Train and compare Logistic Regression, Random Forest, Gradient Boosting, and XGBoost classifiers.
        Selects model with highest PR-AUC score.
        """
        from sklearn.model_selection import train_test_split

        logger.info("Training and evaluating temporal classification models with validation threshold tuning...")
        t0 = time.perf_counter()

        scale_pos_full = (len(y_train) - y_train.sum()) / max(1, y_train.sum())

        # Perform 80/20 train/val split on training data ONLY for decision threshold tuning (zero test set access)
        X_tr, X_val, y_tr, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=self.random_state, stratify=y_train
        )
        scale_pos_tr = (len(y_tr) - y_tr.sum()) / max(1, y_tr.sum())

        model_tr_catalog = {
            "Logistic Regression": LogisticRegression(
                class_weight="balanced", random_state=self.random_state, max_iter=1000
            ),
            "Random Forest Classifier": RandomForestClassifier(
                n_estimators=100, max_depth=6, class_weight="balanced", random_state=self.random_state, n_jobs=-1
            ),
            "Gradient Boosting Classifier": GradientBoostingClassifier(
                n_estimators=50, max_depth=3, random_state=self.random_state
            ),
            "XGBoost Classifier": XGBClassifier(
                n_estimators=50, max_depth=3, scale_pos_weight=scale_pos_tr, random_state=self.random_state
            ),
        }

        full_models = {
            "Logistic Regression": LogisticRegression(
                class_weight="balanced", random_state=self.random_state, max_iter=1000
            ),
            "Random Forest Classifier": RandomForestClassifier(
                n_estimators=100, max_depth=6, class_weight="balanced", random_state=self.random_state, n_jobs=-1
            ),
            "Gradient Boosting Classifier": GradientBoostingClassifier(
                n_estimators=50, max_depth=3, random_state=self.random_state
            ),
            "XGBoost Classifier": XGBClassifier(
                n_estimators=50, max_depth=3, scale_pos_weight=scale_pos_full, random_state=self.random_state
            ),
        }

        comparison: Dict[str, Dict[str, Any]] = {}
        best_model_name = ""
        best_pr_auc = -1.0
        best_model = None

        for name in model_tr_catalog.keys():
            m_t0 = time.perf_counter()
            model_tr = model_tr_catalog[name]

            # 1. Fit on training subset (80% of X_train)
            model_tr.fit(X_tr, y_tr)
            val_probs = model_tr.predict_proba(X_val)[:, 1]

            # 2. Select optimal threshold ON VALIDATION SUBSET ONLY (y_val)
            best_thresh = 0.5
            best_val_f1 = 0.0
            for thresh in np.linspace(0.05, 0.50, 10):
                th_val_preds = (val_probs >= thresh).astype(int)
                th_f1 = f1_score(y_val, th_val_preds, zero_division=0)
                if th_f1 > best_val_f1:
                    best_val_f1 = th_f1
                    best_thresh = thresh

            val_opt_preds = (val_probs >= best_thresh).astype(int)
            val_prec = round(float(precision_score(y_val, val_opt_preds, zero_division=0)), 4)
            val_rec = round(float(recall_score(y_val, val_opt_preds, zero_division=0)), 4)
            val_f1 = round(float(best_val_f1), 4)

            # 3. Fit model on full training set (X_train) and evaluate ONCE on test set (X_test) with FROZEN best_thresh
            full_model = full_models[name]
            full_model.fit(X_train, y_train)
            probs = full_model.predict_proba(X_test)[:, 1]
            preds = (probs >= best_thresh).astype(int)
            m_t_elapsed = time.perf_counter() - m_t0

            roc_auc = round(float(roc_auc_score(y_test, probs)), 4)
            pr_auc = round(float(average_precision_score(y_test, probs)), 4)
            acc = round(float(accuracy_score(y_test, preds)), 4)
            prec = round(float(precision_score(y_test, preds, zero_division=0)), 4)
            rec = round(float(recall_score(y_test, preds, zero_division=0)), 4)
            f1 = round(float(f1_score(y_test, preds, zero_division=0)), 4)
            cm = confusion_matrix(y_test, preds).tolist()

            comparison[name] = {
                "roc_auc": roc_auc,
                "pr_auc": pr_auc,
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
                "optimal_threshold": round(float(best_thresh), 2),
                "validation_metrics": {
                    "val_precision": val_prec,
                    "val_recall": val_rec,
                    "val_f1": val_f1,
                    "optimal_threshold": round(float(best_thresh), 2),
                },
                "confusion_matrix": cm,
                "train_time_sec": round(m_t_elapsed, 4),
            }

            logger.info(
                f"Model '{name}' -> PR-AUC: {pr_auc:.4f} | ROC-AUC: {roc_auc:.4f} | "
                f"Test Rec: {rec*100:.1f}% | Test Prec: {prec*100:.1f}% | Test F1: {f1:.4f} "
                f"(Val-Tuned Thresh: {best_thresh:.2f}, Val F1: {val_f1:.4f}, {m_t_elapsed:.2f}s)"
            )

            if pr_auc > best_pr_auc:
                best_pr_auc = pr_auc
                best_model_name = name
                best_model = full_model

        total_training_time = time.perf_counter() - t0
        logger.info(f"Selected best performing Repeat Purchase model by PR-AUC: '{best_model_name}' (PR-AUC: {best_pr_auc:.4f}).")

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
        Run full temporal Repeat Purchase propensity pipeline:
        Load -> Preprocess -> Train & Evaluate -> Extract Importances -> Predict -> Export Artifacts.
        """
        start_time = time.perf_counter()
        logger.info("Executing Leakage-Free Temporal Repeat Purchase Propensity Pipeline...")

        # 1. Load Data
        df = self.load_data()
        total_customers = len(df)

        class_dist = {
            "non_repeat_count": int((df["target_repeat_buyer"] == 0).sum()),
            "repeat_count": int((df["target_repeat_buyer"] == 1).sum()),
            "repeat_buyer_rate_pct": round(float((df["target_repeat_buyer"] == 1).mean() * 100), 2),
        }
        logger.info(f"Class Distribution: {class_dist['non_repeat_count']:,} non-repeat vs {class_dist['repeat_count']:,} repeat buyers ({class_dist['repeat_buyer_rate_pct']}%).")

        # 2. Preprocess
        X_train, X_test, y_train, y_test, feature_names, full_df = self.preprocess(df)

        num_cols = [
            "obs_recency_days", "obs_frequency_orders", "obs_monetary_value", "obs_avg_order_value",
            "obs_customer_age_days", "obs_total_items", "obs_avg_items_per_order", "obs_avg_freight",
            "obs_avg_delivery_days", "obs_avg_delivery_delay", "obs_late_delivery_ratio",
            "obs_avg_installments", "obs_avg_review_score", "obs_review_count"
        ]
        cat_cols = ["customer_state", "obs_preferred_payment"]

        scaler = StandardScaler().fit(full_df[num_cols].fillna(0.0).values)
        num_scaled_full = scaler.transform(full_df[num_cols].fillna(0.0).values)

        ohe = OneHotEncoder(sparse_output=False, handle_unknown="ignore").fit(full_df[cat_cols].fillna("Unknown").values.astype(str))
        cat_encoded_full = ohe.transform(full_df[cat_cols].fillna("Unknown").values.astype(str))

        X_full = np.hstack([num_scaled_full, cat_encoded_full])

        # 3. Train & Compare Models
        comparison, best_model_name, best_model, training_time = self.train_and_evaluate(
            X_train, X_test, y_train, y_test
        )

        # 4. Extract Top 20 Feature Importances
        top_importances = self.extract_feature_importance(best_model, feature_names, top_n=20)

        # 5. Predict across complete customer dataset
        t_pred_start = time.perf_counter()
        opt_thresh = comparison[best_model_name]["optimal_threshold"]
        probs = best_model.predict_proba(X_full)[:, 1]
        full_df["repeat_purchase_probability"] = probs.round(4)
        full_df["predicted_repeat_buyer"] = (probs >= opt_thresh).astype(int)
        pred_time = time.perf_counter() - t_pred_start

        best_metrics = comparison[best_model_name]

        # 6. Export Artifacts
        if output_dir is None:
            target_dir = self.project_root / "artifacts" / "ml"
        else:
            target_dir = Path(output_dir)

        target_dir.mkdir(parents=True, exist_ok=True)

        csv_path = target_dir / "customer_repeat_purchase_predictions.csv"
        parquet_path = target_dir / "customer_repeat_purchase_predictions.parquet"
        joblib_path = target_dir / "repeat_purchase_pipeline.joblib"

        joblib.dump(
            {
                "model": best_model,
                "model_name": best_model_name,
                "optimal_threshold": opt_thresh,
                "feature_names": feature_names,
                "scaler": scaler,
                "ohe": ohe,
                "num_cols": num_cols,
                "cat_cols": cat_cols,
            },
            joblib_path,
        )
        logger.info(f"Exported joblib Repeat Purchase pipeline -> '{joblib_path.resolve()}'")

        logger.info(f"Exporting CSV predictions artifact -> '{csv_path.resolve()}'")
        full_df.to_csv(csv_path, index=False)

        logger.info(f"Exporting Parquet predictions artifact -> '{parquet_path.resolve()}'")
        full_df.to_parquet(parquet_path, index=False, engine="pyarrow")

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed Repeat Purchase Propensity Pipeline in {elapsed_sec:.4f}s.")

        report = RepeatPurchasePredictionReport(
            total_customers=total_customers,
            class_distribution=class_dist,
            best_model_name=best_model_name,
            best_roc_auc=best_metrics["roc_auc"],
            best_pr_auc=best_metrics["pr_auc"],
            best_accuracy=best_metrics["accuracy"],
            best_precision=best_metrics["precision"],
            best_recall=best_metrics["recall"],
            best_f1_score=best_metrics["f1_score"],
            optimal_threshold=opt_thresh,
            validation_metrics=best_metrics.get("validation_metrics", {}),
            confusion_matrix=best_metrics["confusion_matrix"],
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


if __name__ == "__main__":
    predictor = RepeatPurchasePredictor()
    predictor.run()
