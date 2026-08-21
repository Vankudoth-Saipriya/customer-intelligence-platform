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
    **🎯 BUSINESS QUESTION**: How can we accurately predict 1-year customer lifetime value (CLV) without temporal feature leakage?  
    **📊 KEY INSIGHT**: By enforcing a strict cutoff date (**2017-10-01**), features are generated exclusively from pre-cutoff activity to predict 1-year future spend. **Ridge Regression** achieves an **MAE of $7.27** (Median Absolute Error = **$3.44**).  
    **🔬 EVIDENCE**: Trained on 21,418 observation customers and evaluated on 5,355 chronologically held-out test customers. Top predictive features include `obs_total_items`, `obs_avg_items_per_order`, and `obs_recency_days`.  
    **💡 RECOMMENDED ACTION**: Use predicted CLV tiers to prioritize high-value customer acquisition channels and target high-spend single buyers for post-purchase loyalty rewards.
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

    # Section 1: Model Metrics Bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Temporal Cutoff Date", "2017-10-01")
    with col2:
        st.metric("Model Architecture", clv_meta.get("best_model_name", "Ridge Regression"))
    with col3:
        st.metric("Test Set MAE", f"${clv_meta.get('best_mae', 7.27):.2f}")
    with col4:
        st.metric("Test Set Median AE", f"${clv_meta.get('best_median_ae', 3.44):.2f}")

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
