"""
Unit tests for Advanced Analytics (Cohort Retention, Seller Performance, Pareto Concentration, Inferential Statistical Testing).
"""

import pytest
import pandas as pd
import numpy as np

from app.analytics.advanced_analytics import (
    CohortRetentionAnalyzer,
    SellerPerformanceAnalyzer,
    ParetoRevenueAnalyzer,
    InferentialStatisticalTester,
)


def test_cohort_retention_analyzer():
    """
    Test cohort retention matrix generation and percentage properties.
    """
    analyzer = CohortRetentionAnalyzer()
    mat, pct = analyzer.compute_retention_matrix()

    assert len(mat) > 0
    assert len(pct) > 0

    # Month 0 retention MUST be 100%
    assert (pct[0] == 100.0).all()
    # Relative month retention values must be between 0% and 100%
    assert (pct.fillna(0.0) >= 0.0).all().all()
    assert (pct.fillna(0.0) <= 100.0).all().all()


def test_seller_performance_analyzer():
    """
    Test seller performance aggregation.
    """
    analyzer = SellerPerformanceAnalyzer()
    df = analyzer.analyze_sellers()

    assert len(df) > 0
    assert "seller_id" in df.columns
    assert "total_revenue" in df.columns
    assert "avg_review_score" in df.columns
    assert "late_delivery_rate" in df.columns

    # Revenue and item counts must be non-negative
    assert (df["total_revenue"] >= 0).all()
    assert (df["total_items_sold"] >= 0).all()


def test_pareto_revenue_analyzer():
    """
    Test Pareto 80/20 revenue concentration calculations.
    """
    analyzer = ParetoRevenueAnalyzer()
    res = analyzer.analyze_concentration()

    assert "customer_concentration" in res
    assert "seller_concentration" in res

    cust = res["customer_concentration"]
    seller = res["seller_concentration"]

    assert cust["total_customers"] > 0
    assert cust["total_revenue"] > 0
    assert 0 <= cust["top_20_percent_revenue_share"] <= 100

    assert seller["total_sellers"] > 0
    assert seller["total_revenue"] > 0
    assert 0 <= seller["top_20_percent_revenue_share"] <= 100


def test_inferential_statistical_tests():
    """
    Test inferential hypothesis testing routines and outputs.
    """
    tester = InferentialStatisticalTester()

    # Test 1: Delivery Delay vs Review Score
    res1 = tester.test_delivery_delay_vs_satisfaction()
    assert "p_value" in res1
    assert 0.0 <= res1["p_value"] <= 1.0
    assert "effect_size_rank_biserial" in res1
    assert res1["statistically_significant"] is True

    # Test 2: Repeat Buyer Spend Difference
    res2 = tester.test_repeat_buyer_spend_difference()
    assert "p_value" in res2
    assert 0.0 <= res2["p_value"] <= 1.0

    # Test 3: Regional Delivery Delay ANOVA/Kruskal-Wallis
    res3 = tester.test_state_delivery_delay_anova()
    assert "p_value" in res3
    assert 0.0 <= res3["p_value"] <= 1.0
    assert len(res3["evaluated_states"]) == 5
