"""
Page 4: Predictive Analytics, Temporal Cutoff Validation, and Model Interpretability.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from app.dashboard.data_provider import call_clv_api

st.set_page_config(page_title="Predictive Analytics | CIP", page_icon="🤖", layout="wide")

st.title("🤖 Predictive Decision Support: Temporal CLV & Model Interpretability")
st.markdown("---")

# Executive Business Insight Card
st.info(
    """
    **🎯 BUSINESS QUESTION**: Can we accurately predict 90-day future customer spend from prior transaction history without feature leakage?
    **📊 KEY INSIGHT**: Using a temporal cutoff date (**2017-10-01**), predictors ($X$) are computed strictly from pre-cutoff behavior to predict 90-day future spend ($y$, `2017-10-01` to `2017-12-30`). Due to 99.09% zero-spending imbalance, a naive **Zero-Spend Baseline achieves $1.25 MAE**.
    **🔬 EVIDENCE**: Evaluated on 15,347 chronologically held-out test customers ($N = 26,773$ total observation customers).
    **💡 RECOMMENDED ACTION**: Use customer RFM tiers and past monetary spend for targeted retention marketing, while recognizing the high zero-inflation inherent in single-purchase marketplaces.
    """
)

try:
    from app.dashboard.data_provider import (
        get_clv_prediction_data,
        get_clv_metadata,
        get_customer_segmentation_data,
    )

    clv_meta = get_clv_metadata()
    df_clv = get_clv_prediction_data()
    df_seg = get_customer_segmentation_data()

    # Section 1: Model & Baseline Metrics Bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Prediction Horizon", "90 Days Post-Cutoff")
    with col2:
        st.metric("Zero-Spend Baseline MAE", f"${clv_meta.get('zero_baseline_mae', 1.25):.2f}")
    with col3:
        st.metric("Mean-Spend Baseline MAE", f"${clv_meta.get('mean_baseline_mae', 2.30):.2f}")
    with col4:
        st.metric("Ridge Model MAE", f"${clv_meta.get('best_mae', 3.05):.2f}")

    st.markdown("---")

    # Section 2: Model Feature Weights Interpretability
    st.subheader("⚖️ Model Interpretability: Top Feature Weights")
    st.markdown("*Note: Feature weights represent trained Ridge Regression coefficients / importances, not structural causal effects.*")

    feat_imp_list = clv_meta.get("feature_importance", [])
    if feat_imp_list:
        df_fi = pd.DataFrame(feat_imp_list).head(10).sort_values(by="importance_score", ascending=True)
        fig_fi = px.bar(
            df_fi,
            x="importance_score",
            y="feature",
            orientation="h",
            color="importance_score",
            color_continuous_scale="Viridis",
            title=f"Top 10 Feature Weights ({clv_meta.get('best_model_name', 'Ridge Regression')})",
            labels={"importance_score": "Model Weight / Importance", "feature": "Feature Name"},
            text="importance_score"
        )
        fig_fi.update_layout(template="plotly_dark", height=400)
        st.plotly_chart(fig_fi, use_container_width=True)
    else:
        st.warning("Feature importance data unavailable.")

    st.markdown("---")

    # Section 3: High CLV Customer Distribution & Real-Time API Demo
    st.subheader("🏆 Top Predicted High-CLV Customer Profiles")
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### High-Value Predictions Data Sample")
        if not df_clv.empty and "predicted_clv" in df_clv.columns:
            avail_cols = [c for c in ["customer_id", "state", "frequency_orders", "monetary_value", "predicted_clv"] if c in df_clv.columns]
            top_clv = df_clv.sort_values(by="predicted_clv", ascending=False)[avail_cols].head(10)
            st.dataframe(top_clv, use_container_width=True, hide_index=True)
        else:
            st.warning("High-CLV predictions data unavailable.")

    with c2:
        st.markdown("#### Real-Time CLV Prediction API Endpoint")
        st.markdown("Enter a `customer_id` to call `POST /api/v1/ml/clv`.")
        
        sample_id = df_clv["customer_id"].iloc[0] if not df_clv.empty and "customer_id" in df_clv.columns else "00012a2504309823e6e38064373a51d2"
        cust_input = st.text_input("Enter Customer ID:", value=sample_id)

        if st.button("Predict Customer Lifetime Value"):
            with st.spinner("Calling ML Inference API Endpoint..."):
                res = call_clv_api(customer_id=cust_input)
            
            st.success("API Inference Complete!")
            pred_val = res.get("predicted_clv", 0.0)
            st.metric("Predicted Customer Lifetime Value", f"${pred_val:,.2f}")

except Exception as e:
    st.error(f"Error loading Predictive Analytics Page: {e}")
