"""
Customer Lifetime Value (CLV) Prediction ML Module.

Trains and evaluates regression models to predict customer total revenue:
- Target: total_revenue
- Models: Linear Regression, Random Forest Regressor, Gradient Boosting Regressor
- Data Split: 80/20 train/test split (random_state=42)
- Evaluates MAE, RMSE, R² and selects highest R² model
- Computes Top 20 Feature Importances
- Exports Parquet, CSV predictions and JSON metadata artifacts
"""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.report import CustomerCLVReport


class CustomerLifetimeValuePredictor:
    """
    ML Pipeline for predicting Customer Lifetime Value (CLV / Total Revenue).
    """

    def __init__(
        self,
        feature_store_path: Optional[Path] = None,
        random_state: int = 42,
    ) -> None:
        """
        Initialize CustomerLifetimeValuePredictor pipeline.
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
        Preprocess feature table for regression modeling:
        - Target: total_revenue
        - Exclude identifiers & target leakage columns
        - One-hot encode categoricals, standard scale numerics
        - Train/Test Split (80/20, random_state=42)
        """
        logger.info("Preprocessing features for CLV Prediction (removing leakage, OHE, Scaling, 80/20 split)...")

        target_col = "total_revenue"
        if target_col not in df.columns:
            raise KeyError(f"Target column '{target_col}' missing from feature store!")

        y = df[target_col].values.astype(float)

        exclude_cols = [
            "customer_id",
            "customer_unique_id",
            "first_purchase_date",
            "last_purchase_date",
            "city",
            "total_revenue",
            "monetary_value",
            "revenue_rank_percentile",
            "customer_value_tier",
            "spending_velocity",
        ]

        feature_cols = [c for c in df.columns if c not in exclude_cols]

        cat_cols = ["state", "favorite_product_category", "preferred_payment_method"]
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
            X, y, test_size=0.20, random_state=self.random_state
        )

        logger.info(f"Split dataset into Train: {len(X_train):,} rows, Test: {len(X_test):,} rows across {X.shape[1]} features.")
        return X_train, X_test, y_train, y_test, feature_names, df

    def train_and_evaluate(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
    ) -> Tuple[Dict[str, Dict[str, float]], str, Any, float]:
        """
        Train and compare Linear Regression, Random Forest, and Gradient Boosting models.
        Selects best model based on highest test R² score.
        """
        logger.info("Training and evaluating regression models...")
        t0 = time.perf_counter()

        models = {
            "Linear Regression": LinearRegression(),
            "Random Forest Regressor": RandomForestRegressor(
                n_estimators=100, max_depth=12, random_state=self.random_state, n_jobs=-1
            ),
            "Gradient Boosting Regressor": GradientBoostingRegressor(
                n_estimators=50, max_depth=4, random_state=self.random_state
            ),
        }

        comparison: Dict[str, Dict[str, float]] = {}
        best_model_name = ""
        best_r2 = -float("inf")
        best_model = None

        for name, model in models.items():
            m_t0 = time.perf_counter()
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            m_t_elapsed = time.perf_counter() - m_t0

            mae = round(float(mean_absolute_error(y_test, preds)), 4)
            rmse = round(float(np.sqrt(mean_squared_error(y_test, preds))), 4)
            r2 = round(float(r2_score(y_test, preds)), 4)

            comparison[name] = {
                "mae": mae,
                "rmse": rmse,
                "r2_score": r2,
                "train_time_sec": round(m_t_elapsed, 4),
            }

            logger.info(f"Model '{name}' -> R²: {r2:.4f} | RMSE: {rmse:.4f} | MAE: {mae:.4f} ({m_t_elapsed:.2f}s)")

            if r2 > best_r2:
                best_r2 = r2
                best_model_name = name
                best_model = model

        total_training_time = time.perf_counter() - t0
        logger.info(f"Best performing model selected by R²: '{best_model_name}' (R²: {best_r2:.4f}).")

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
            importances = np.abs(model.coef_)
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
        Run full CLV prediction pipeline:
        Load -> Preprocess -> Train & Evaluate -> Extract Importances -> Predict -> Export Artifacts.
        """
        start_time = time.perf_counter()
        logger.info("Executing Customer Lifetime Value (CLV) Prediction Pipeline...")

        # 1. Load Data
        df = self.load_data()
        total_customers = len(df)

        # 2. Preprocess
        X_train, X_test, y_train, y_test, feature_names, full_df = self.preprocess(df)

        cat_cols = ["state", "favorite_product_category", "preferred_payment_method"]
        exclude_cols = [
            "customer_id", "customer_unique_id", "first_purchase_date", "last_purchase_date",
            "city", "total_revenue", "monetary_value", "revenue_rank_percentile",
            "customer_value_tier", "spending_velocity"
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
        full_df["predicted_clv"] = best_model.predict(X_full).round(2)
        full_df["clv_error"] = (full_df["predicted_clv"] - full_df["total_revenue"]).round(2)
        pred_time = time.perf_counter() - t_pred_start

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
