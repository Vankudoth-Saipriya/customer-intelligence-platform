"""
Test script for CustomerFeatureStore.
"""

from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.features.customer_feature_store import CustomerFeatureStore


def test_customer_feature_store():
    project_root = Path(__file__).resolve().parent.parent
    db_path = project_root / "artifacts" / "customer_intelligence_verification.db"
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        feature_store = CustomerFeatureStore(session=session)
        report = feature_store.build_feature_store()

        print("Customer Feature Store pipeline complete!")
        print(f"Total Customers: {report.total_customers:,}")
        print(f"Total Features: {report.total_features}")
        print(f"Parquet Artifact Path: {report.parquet_path}")
        print(f"CSV Artifact Path: {report.csv_path}")
        print(f"Metadata Artifact Path: {report.metadata_path}")
        print(f"Execution Time: {report.execution_time_sec:.4f}s")

        # Verify artifacts on disk
        pq_path = Path(report.parquet_path)
        csv_path = Path(report.csv_path)
        json_path = Path(report.metadata_path)

        assert pq_path.exists(), "Parquet artifact missing!"
        assert csv_path.exists(), "CSV artifact missing!"
        assert json_path.exists(), "Metadata artifact missing!"

        # Read back parquet and verify
        df_pq = pd.read_parquet(pq_path)
        print(f"Verified Parquet DataFrame shape: {df_pq.shape}")
        assert len(df_pq) == report.total_customers
        assert df_pq["customer_id"].nunique() == report.total_customers
        assert df_pq["customer_id"].isnull().sum() == 0


if __name__ == "__main__":
    test_customer_feature_store()
