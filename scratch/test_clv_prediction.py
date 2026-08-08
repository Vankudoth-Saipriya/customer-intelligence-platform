"""
Test script for CustomerLifetimeValuePredictor.
"""

from pathlib import Path
import pandas as pd
from app.ml.clv_prediction import CustomerLifetimeValuePredictor


def test_clv_prediction():
    predictor = CustomerLifetimeValuePredictor()
    report = predictor.run()

    print("CLV Prediction execution complete!")
    print(f"Total Customers Evaluated: {report.total_customers:,}")
    print(f"Best Performing Model: {report.best_model_name}")
    print(f"Best R² Score: {report.best_r2_score}")
    print(f"Best RMSE: {report.best_rmse}")
    print(f"Best MAE: {report.best_mae}")
    print(f"CSV Artifact Path: {report.csv_path}")
    print(f"Parquet Artifact Path: {report.parquet_path}")
    print(f"Metadata Artifact Path: {report.metadata_path}")
    print(f"Execution Time: {report.execution_time_sec:.4f}s")

    # Verify artifacts on disk
    csv_path = Path(report.csv_path)
    pq_path = Path(report.parquet_path)
    json_path = Path(report.metadata_path)

    assert csv_path.exists(), "CSV artifact missing!"
    assert pq_path.exists(), "Parquet artifact missing!"
    assert json_path.exists(), "Metadata artifact missing!"

    df_clv = pd.read_parquet(pq_path)
    print(f"Verified CLV Predictions DataFrame shape: {df_clv.shape}")
    assert len(df_clv) == report.total_customers
    assert "predicted_clv" in df_clv.columns
    assert "clv_error" in df_clv.columns
    assert df_clv["predicted_clv"].isnull().sum() == 0


if __name__ == "__main__":
    test_clv_prediction()
