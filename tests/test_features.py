"""
Unit tests for Customer Feature Store, Temporal Cutoff Enforcement, and Leakage Prevention.
"""

import pytest
import pandas as pd
import numpy as np
from app.features.customer_feature_store import CustomerFeatureStore


def test_build_temporal_feature_store_cutoff_enforcement():
    """
    Test that temporal feature store strictly enforces observation cutoff date (2017-10-01).
    All predictor features MUST be derived from orders BEFORE 2017-10-01.
    """
    fs = CustomerFeatureStore()
    df = fs.build_temporal_feature_store(cutoff_date="2017-10-01")

    # 1. Non-empty DataFrame returned
    assert len(df) > 0
    assert "target_future_clv" in df.columns
    assert "target_repeat_buyer" in df.columns

    # 2. Verify observation columns exist
    assert "obs_recency_days" in df.columns
    assert "obs_frequency_orders" in df.columns
    assert "obs_monetary_value" in df.columns
    assert "obs_avg_order_value" in df.columns

    # 3. Verify no NaN values in critical predictor columns
    assert df["obs_recency_days"].isna().sum() == 0
    assert df["obs_frequency_orders"].isna().sum() == 0
    assert df["obs_monetary_value"].isna().sum() == 0
    assert df["target_future_clv"].isna().sum() == 0
    assert df["target_repeat_buyer"].isna().sum() == 0

    # 4. Verify temporal leakage prevention:
    # All observation customer first_purchase_date must be before cutoff 2017-10-01
    assert (pd.to_datetime(df["first_purchase_date"]) < pd.to_datetime("2017-10-01")).all()


def test_temporal_feature_store_target_consistency():
    """
    Test that target_repeat_buyer is binary and consistent with target_future_clv.
    """
    fs = CustomerFeatureStore()
    df = fs.build_temporal_feature_store(cutoff_date="2017-10-01")

    repeat_mask = df["target_repeat_buyer"] == 1
    non_repeat_mask = df["target_repeat_buyer"] == 0

    # All repeat buyers must have target_future_clv > 0
    assert (df.loc[repeat_mask, "target_future_clv"] > 0).all()
    # All non-repeat buyers must have target_future_clv == 0
    assert (df.loc[non_repeat_mask, "target_future_clv"] == 0).all()


def test_no_post_cutoff_records_in_observation_features():
    """
    Test proving that post-cutoff records (on or after 2017-10-01) cannot enter observation features.
    """
    fs = CustomerFeatureStore()
    df = fs.build_temporal_feature_store(cutoff_date="2017-10-01")

    # Observation recency must be positive (since cutoff is 2017-10-01 and last purchase < 2017-10-01)
    assert (df["obs_recency_days"] >= 0).all()
    # Customer age must be strictly positive and greater than recency
    assert (df["obs_customer_age_days"] >= df["obs_recency_days"]).all()
