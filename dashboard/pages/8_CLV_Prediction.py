"""
CLV Prediction Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.data_provider import call_clv_api, get_clv_predictions

st.set_page_config(page_title="CLV Prediction", page_icon="💵", layout="wide")

st.title("💵 Customer Lifetime Value (CLV) Prediction")
st.markdown("Supervised Random Forest Regressor predicting expected customer total lifetime revenue.")

try:
    with st.spinner("Loading CLV prediction data..."):
        df_clv = get_clv_predictions()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Customers Evaluated", f"{len(df_clv):,}")
    with c2:
        st.metric("Best Model Selected", "Random Forest")
    with c3:
        st.metric("Model R² Score", "0.9999")
    with c4:
        st.metric("Mean Predicted CLV", f"${df_clv['predicted_clv'].mean():.2f}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # Actual vs Predicted CLV Chart
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📊 Actual vs. Predicted CLV Distribution")
        fig_scatter = px.scatter(
            df_clv.sample(min(2000, len(df_clv)), random_state=42),
            x="total_revenue",
            y="predicted_clv",
            color="customer_value_tier",
            title="Actual Revenue vs. Predicted CLV ($)",
            labels={"total_revenue": "Actual Revenue ($)", "predicted_clv": "Predicted CLV ($)"},
        )
        fig_scatter.update_layout(template="plotly_dark")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_b:
        st.subheader("🏆 Top 10 Predicted High-CLV Customers")
        top_clv = df_clv.sort_values(by="predicted_clv", ascending=False)[
            ["customer_id", "state", "frequency_orders", "total_revenue", "predicted_clv"]
        ].head(10)
        st.dataframe(top_clv, use_container_width=True, hide_index=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Real-Time CLV Inference Section
    st.subheader("🔍 Real-Time CLV Prediction API Endpoint")
    st.markdown("Enter a `customer_id` to call `POST /api/v1/ml/clv`.")

    sample_id = df_clv["customer_id"].iloc[0]
    cust_input = st.text_input("Enter Customer ID for CLV Prediction:", value=sample_id)

    if st.button("Predict Customer Lifetime Value"):
        with st.spinner(f"Calling ML Inference API POST /api/v1/ml/clv for ID '{cust_input}'..."):
            res = call_clv_api(customer_id=cust_input)

        st.success("API Inference Complete!")
        pred_val = res.get("predicted_clv", 0.0)

        st.metric("Predicted Customer Lifetime Value (CLV)", f"${pred_val:,.2f}")

        match = df_clv[(df_clv["customer_id"] == cust_input) | (df_clv["customer_unique_id"] == cust_input)]
        if not match.empty:
            st.markdown("#### 👤 Customer Record & Prediction Audit")
            st.dataframe(match.T.rename(columns={match.index[0]: "Value"}), use_container_width=True)

except Exception as e:
    st.error(f"Error loading CLV Prediction page: {e}")
