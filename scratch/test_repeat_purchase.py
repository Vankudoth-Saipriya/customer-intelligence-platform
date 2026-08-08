"""
Test script for RepeatPurchasePredictor.
"""

from pathlib import Path
import pandas as pd
from app.ml.repeat_purchase_prediction import RepeatPurchasePredictor


def test_repeat_purchase_prediction():
    predictor = RepeatPurchasePredictor()
    report = predictor.run()

    print("Repeat Purchase Propensity execution complete!")
    print(f"Total Customers Evaluated: {report.total_customers:,}")
    print(f"Class Distribution: {report.class_distribution}")
    print(f"Best Performing Model: {report.best_model_name}")
    print(f"Best ROC-AUC: {report.best_roc_auc}")
    print(f"Best F1 Score: {report.best_f1_score}")
    print(f"Best Accuracy: {report.best_accuracy}")
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

    df_preds = pd.read_parquet(pq_path)
    print(f"Verified Repeat Predictions DataFrame shape: {df_preds.shape}")
    assert len(df_preds) == report.total_customers
    assert "repeat_propensity" in df_preds.columns
    assert "predicted_repeat_customer" in df_preds.columns
    assert df_preds["repeat_propensity"].isnull().sum() == 0


if __name__ == "__main__":
    test_repeat_purchase_prediction()
