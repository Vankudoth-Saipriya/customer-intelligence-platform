"""
Unit and integration tests for ML Pipelines (CLV, Repeat Purchase, Segmentation).
"""

import pytest
from pathlib import Path
import pandas as pd
import numpy as np

from app.ml.clv_prediction import CustomerLifetimeValuePredictor
from app.ml.repeat_purchase_prediction import RepeatPurchasePredictor
from app.ml.segmentation import CustomerSegmentation


def test_clv_predictor_pipeline():
    """
    Test end-to-end execution of temporal CLV prediction pipeline (cutoff 2017-10-01).
    """
    predictor = CustomerLifetimeValuePredictor(cutoff_date="2017-10-01")
    report = predictor.run()

    assert report.total_customers > 0
    assert report.best_model_name in [
        "Ridge Regression", "Random Forest Regressor", "Gradient Boosting Regressor",
        "XGBoost Regressor", "Hurdle Model (Two-Stage GBDT+Ridge)"
    ]
    assert report.best_mae >= 0
    assert len(report.feature_importance) > 0

    # Verify predictions file exists
    assert Path(report.parquet_path).exists()


def test_repeat_purchase_predictor_pipeline():
    """
    Test end-to-end execution of temporal Repeat Purchase prediction pipeline (cutoff 2017-10-01).
    """
    predictor = RepeatPurchasePredictor(cutoff_date="2017-10-01")
    report = predictor.run()

    assert report.total_customers > 0
    assert report.best_model_name in [
        "Logistic Regression", "Random Forest Classifier", "Gradient Boosting Classifier", "XGBoost Classifier"
    ]
    assert report.best_roc_auc >= 0.0
    assert report.best_pr_auc >= 0.0
    assert len(report.confusion_matrix) == 2

    assert Path(report.parquet_path).exists()


def test_customer_segmentation_pipeline():
    """
    Test RFM Customer Segmentation pipeline for K=4 personas.
    """
    segmenter = CustomerSegmentation()
    report = segmenter.run()

    assert report.total_customers_segmented > 0
    assert report.best_k == 4
    assert len(report.cluster_profiles) == 4
    assert "cluster_0" in report.cluster_profiles
    assert "cluster_3" in report.cluster_profiles

    assert Path(report.parquet_path).exists()
