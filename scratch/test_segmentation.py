"""
Test script for CustomerSegmentation.
"""

from pathlib import Path
import pandas as pd
from app.ml.segmentation import CustomerSegmentation


def test_customer_segmentation():
    segmenter = CustomerSegmentation()
    report = segmenter.run()

    print("Customer Segmentation execution complete!")
    print(f"Total Customers Segmented: {report.total_customers_segmented:,}")
    print(f"Selected Optimal k: {report.best_k}")
    print(f"Best Silhouette Score: {report.best_silhouette_score}")
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

    df_seg = pd.read_parquet(pq_path)
    print(f"Verified Segmented DataFrame shape: {df_seg.shape}")
    assert len(df_seg) == report.total_customers_segmented
    assert "cluster_id" in df_seg.columns
    assert "cluster_description" in df_seg.columns
    assert df_seg["cluster_id"].isnull().sum() == 0


if __name__ == "__main__":
    test_customer_segmentation()
