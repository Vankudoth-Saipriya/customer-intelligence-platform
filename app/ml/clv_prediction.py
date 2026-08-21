"""
Customer Lifetime Value (CLV) Prediction ML Module.

Trains and evaluates leakage-free temporal regression models to predict future customer total revenue:
- Observation Cutoff: 2017-10-01
- Observation Period: Dataset start (2016-09-04) through 2017-10-01 (~12.8 months)
- Prediction Horizon: 2017-10-01 through dataset end 2018-10-17 (~12.5 months)
- Target: target_future_clv (Future revenue spent between 2017-10-01 and 2018-10-17)
- Predictors: Engineered strictly from orders placed BEFORE 2017-10-01
- Data Split: Chronological Train/Test split (Train: acquisition < 2017-06-01, Test: >= 2017-06-01 and < 2017-10-01)
- Models Evaluated: Ridge Regression, Random Forest Regressor, Gradient Boosting Regressor, XGBoost Regressor, Hurdle (Two-Stage GBDT+Ridge)
- Metrics: RMSE, MAE, R², Median Absolute Error, Non-Zero Target MAE
- Exports Parquet, CSV predictions and JSON metadata artifacts
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
import numpy as np
import pandas as pd
import joblib

from sklearn.linear_model import Ridge
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, median_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.features.customer_feature_store import CustomerFeatureStore
from app.ml.report import CustomerCLVReport


class HurdleCLVRegressor:
    """
    Two-Stage Hurdle Model for zero-inflated CLV:
    - Stage 1: GBDT Classifier P(Future Spend > 0)
    - Stage 2: Ridge Regressor E(Future Spend | Future Spend > 0)
    """

    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.clf = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=random_state)
        self.reg = Ridge(alpha=1.0, random_state=random_state)

    def fit(self, X: np.ndarray, y: np.ndarray) -> "HurdleCLVRegressor":
        y_binary = (y > 0).astype(int)
        self.clf.fit(X, y_binary)
        pos_mask = y > 0
        if pos_mask.sum() > 5:
            self.reg.fit(X[pos_mask], y[pos_mask])
        else:
            self.reg.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        prob = self.clf.predict_proba(X)[:, 1]
        cond_pred = np.maximum(0.0, self.reg.predict(X))
        return prob * cond_pred


class CustomerLifetimeValuePredictor:
    """
    ML Pipeline for predicting Customer Lifetime Value (CLV / Future Revenue).
    """

    def __init__(
        self,
        cutoff_date: str = "2017-10-01",
        random_state: int = 42,
    ) -> None:
        """
        Initialize CustomerLifetimeValuePredictor pipeline.
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
        Preprocess temporal feature table for regression modeling:
        - Target: target_future_clv
        - Chronological Train/Test Split:
            - Train: first_purchase_date < 2017-06-01
            - Test: first_purchase_date >= 2017-06-01 and < 2017-10-01
        - Preprocessing: One-hot encode categoricals, standard scale numerics
        """
        logger.info("Preprocessing features for CLV Prediction (chronological split, OHE, Scaling)...")

        df = df.copy()
        df.columns = [str(c) for c in df.columns]

        target_col = "target_future_clv"
        if target_col not in df.columns:
            raise KeyError(f"Target column '{target_col}' missing from feature store!")

        # Define predictors strictly from observation window
        num_cols = [
            "obs_recency_days", "obs_frequency_orders", "obs_monetary_value", "obs_avg_order_value",
            "obs_customer_age_days", "obs_total_items", "obs_avg_items_per_order", "obs_avg_freight",
            "obs_avg_delivery_days", "obs_avg_delivery_delay", "obs_late_delivery_ratio",
            "obs_avg_installments", "obs_avg_review_score", "obs_review_count"
        ]
        cat_cols = ["customer_state", "obs_preferred_payment"]

        # Chronological Train/Test Split (Train: acquired < 2017-06-01, Test: acquired >= 2017-06-01)
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

        y_train = train_df[target_col].values.astype(float)
        y_test = test_df[target_col].values.astype(float)

        feature_names = num_cols + encoded_cat_feature_names

        logger.info(f"Chronological Split -> Train: {len(X_train):,} rows (< {split_dt}), Test: {len(X_test):,} rows (>= {split_dt}) across {X_train.shape[1]} features.")
        return X_train, X_test, y_train, y_test, feature_names, df

    def train_and_evaluate(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
    ) -> Tuple[Dict[str, Dict[str, float]], str, Any, float]:
        """
        Train and compare Ridge Regression, Random Forest, Gradient Boosting, XGBoost, and Hurdle models.
        Selects model with lowest test MAE.
        """
        logger.info("Training and evaluating temporal CLV regression models...")
        t0 = time.perf_counter()

        models = {
            "Ridge Regression": Ridge(alpha=1.0, random_state=self.random_state),
            "Random Forest Regressor": RandomForestRegressor(
                n_estimators=100, max_depth=6, random_state=self.random_state, n_jobs=-1
            ),
            "Gradient Boosting Regressor": GradientBoostingRegressor(
                n_estimators=50, max_depth=3, random_state=self.random_state
            ),
            "XGBoost Regressor": XGBRegressor(
                n_estimators=50, max_depth=3, random_state=self.random_state
            ),
            "Hurdle Model (Two-Stage GBDT+Ridge)": HurdleCLVRegressor(
                random_state=self.random_state
            ),
        }

        comparison: Dict[str, Dict[str, float]] = {}
        best_model_name = ""
        best_mae = float("inf")
        best_model = None

        pos_mask = y_test > 0

        for name, model in models.items():
            m_t0 = time.perf_counter()
            model.fit(X_train, y_train)
            preds = np.maximum(0.0, model.predict(X_test))
            m_t_elapsed = time.perf_counter() - m_t0

            mae = round(float(mean_absolute_error(y_test, preds)), 4)
            rmse = round(float(np.sqrt(mean_squared_error(y_test, preds))), 4)
            r2 = round(float(r2_score(y_test, preds)), 4)
            med_ae = round(float(median_absolute_error(y_test, preds)), 4)
            non_zero_mae = round(float(mean_absolute_error(y_test[pos_mask], preds[pos_mask])), 4) if pos_mask.sum() > 0 else 0.0

            comparison[name] = {
                "mae": mae,
                "rmse": rmse,
                "r2_score": r2,
                "median_absolute_error": med_ae,
                "non_zero_clv_mae": non_zero_mae,
                "train_time_sec": round(m_t_elapsed, 4),
            }

            logger.info(f"Model '{name}' -> MAE: ${mae:.2f} | MedAE: ${med_ae:.2f} | RMSE: ${rmse:.2f} | R²: {r2:.4f} | NonZero MAE: ${non_zero_mae:.2f} ({m_t_elapsed:.2f}s)")

            if mae < best_mae:
                best_mae = mae
                best_model_name = name
                best_model = model

        total_training_time = time.perf_counter() - t0
        logger.info(f"Selected best performing CLV model by MAE: '{best_model_name}' (MAE: ${best_mae:.2f}).")

        return comparison, best_model_name, best_model, total_training_time

    def extract_feature_importance(
        self, model: Any, feature_names: List[str], top_n: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Extract top N feature importances or coefficient absolute weights from the selected model.
        """
        target_model = getattr(model, "regressor", getattr(model, "reg", model))

        if hasattr(target_model, "feature_importances_"):
            importances = target_model.feature_importances_
        elif hasattr(target_model, "coef_"):
            importances = np.abs(target_model.coef_)
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

    def run(self, output_dir: Optional[Path] = None) -> CustomerCLVReport:
        """
        Run full temporal CLV prediction pipeline:
        Load -> Preprocess -> Train & Evaluate -> Extract Importances -> Predict -> Export Artifacts.
        """
        start_time = time.perf_counter()
        logger.info("Executing Leakage-Free Temporal Customer Lifetime Value (CLV) Prediction Pipeline...")

        # 1. Load Data
        df = self.load_data()
        total_customers = len(df)

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
        full_df["predicted_clv"] = np.maximum(0.0, best_model.predict(X_full)).round(2)
        full_df["clv_error"] = (full_df["predicted_clv"] - full_df["target_future_clv"]).round(2)
        pred_time = time.perf_counter() - t_pred_start

        # Log Top Over & Under Predictions
        full_df_sorted = full_df.sort_values(by="clv_error", ascending=False)
        top_over = full_df_sorted.head(5)[["customer_unique_id", "obs_monetary_value", "target_future_clv", "predicted_clv", "clv_error"]]
        top_under = full_df_sorted.tail(5)[["customer_unique_id", "obs_monetary_value", "target_future_clv", "predicted_clv", "clv_error"]]
        logger.info(f"Top 5 Over-Predictions:\n{top_over.to_string(index=False)}")
        logger.info(f"Top 5 Under-Predictions:\n{top_under.to_string(index=False)}")

        best_metrics = comparison[best_model_name]

        # 6. Export Artifacts
        if output_dir is None:
            target_dir = self.project_root / "artifacts" / "ml"
        else:
            target_dir = Path(output_dir)

        target_dir.mkdir(parents=True, exist_ok=True)

        csv_path = target_dir / "customer_clv_predictions.csv"
        parquet_path = target_dir / "customer_clv_predictions.parquet"
        joblib_path = target_dir / "clv_pipeline.joblib"

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
        logger.info(f"Exported joblib CLV pipeline -> '{joblib_path.resolve()}'")

        logger.info(f"Exporting CSV predictions artifact -> '{csv_path.resolve()}'")
        full_df.to_csv(csv_path, index=False)

        logger.info(f"Exporting Parquet predictions artifact -> '{parquet_path.resolve()}'")
        full_df.to_parquet(parquet_path, index=False, engine="pyarrow")

        elapsed_sec = time.perf_counter() - start_time
        logger.info(f"Completed CLV Prediction Pipeline in {elapsed_sec:.4f}s.")

        report = CustomerCLVReport(
            total_customers=total_customers,
            best_model_name=best_model_name,
            best_r2_score=best_metrics["r2_score"],
            best_rmse=best_metrics["rmse"],
            best_mae=best_metrics["mae"],
            best_median_ae=best_metrics["median_absolute_error"],
            best_non_zero_clv_mae=best_metrics["non_zero_clv_mae"],
            model_comparison=comparison,
            feature_importance=top_importances,
            csv_path=str(csv_path.resolve()),
            parquet_path=str(parquet_path.resolve()),
            metadata_path="",
            training_time_sec=round(training_time, 4),
            prediction_time_sec=round(pred_time, 4),
            execution_time_sec=round(elapsed_sec, 4),
        )

        # Save metadata report to artifacts/ml/customer_clv_metadata.json
        report.save_json()

        return report


if __name__ == "__main__":
    predictor = CustomerLifetimeValuePredictor()
    predictor.run()
