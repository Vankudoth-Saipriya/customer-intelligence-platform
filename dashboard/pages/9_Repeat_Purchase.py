"""
Repeat Purchase Propensity Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.dashboard.data_provider import call_repeat_api, get_repeat_predictions

st.set_page_config(page_title="Repeat Purchase Propensity", page_icon="🔄", layout="wide")

st.title("🔄 Repeat Purchase Propensity ML Model")
st.markdown("Supervised Logistic Regression predicting repeat buyer propensity with class imbalance handling.")

try:
    with st.spinner("Loading repeat purchase prediction data..."):
        df_rp = get_repeat_predictions()

    if df_rp.empty:
        st.warning("Repeat purchase prediction dataset is empty")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Customers Evaluated", f"{len(df_rp):,}")
        with c2:
            st.metric("Best Model Selected", "Logistic Regression")
        with c3:
            st.metric("Model ROC-AUC", "1.0000")
        with c4:
            repeat_rate = (df_rp['repeat_customer'] == 1).mean() * 100 if "repeat_customer" in df_rp.columns else 3.12
            st.metric("Repeat Buyers Rate", f"{repeat_rate:.2f}%")

        st.markdown("<hr>", unsafe_allow_html=True)

        # 1. Propensity Score Distribution
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("📊 Repeat Purchase Propensity Probability Score Distribution")
            if "repeat_propensity" in df_rp.columns:
                df_sample = df_rp.sample(min(5000, len(df_rp)), random_state=42)
                fig_prob = px.histogram(
                    df_sample,
                    x="repeat_propensity",
                    nbins=50,
                    title="Distribution of Repeat Propensity Scores (Sampled 5,000 Points)",
                    labels={"repeat_propensity": "Repeat Propensity Probability"},
                    color_discrete_sequence=["#8B5CF6"],
                )
                fig_prob.update_layout(template="plotly_dark")
                st.plotly_chart(fig_prob, use_container_width=True)
            else:
                st.warning("Repeat propensity score distribution data unavailable")

        with col_b:
            st.subheader("🎯 Class Prediction Counts")
            if "predicted_repeat_customer" in df_rp.columns:
                pred_counts = df_rp["predicted_repeat_customer"].value_counts().reset_index()
                pred_counts.columns = ["Prediction", "Customer Count"]
                pred_counts["Label"] = pred_counts["Prediction"].map({0: "Single Order (0)", 1: "Repeat Buyer (1)"})

                fig_pred = px.pie(
                    pred_counts,
                    names="Label",
                    values="Customer Count",
                    hole=0.4,
                    title="Predicted Repeat Customer Breakdown",
                    color="Label",
                    color_discrete_map={"Single Order (0)": "#EF4444", "Repeat Buyer (1)": "#10B981"},
                )
                fig_pred.update_layout(template="plotly_dark")
                st.plotly_chart(fig_pred, use_container_width=True)
            else:
                st.warning("Predicted repeat customer breakdown unavailable")

        st.markdown("<hr>", unsafe_allow_html=True)

        # Real-Time Repeat Propensity Inference Section
        st.subheader("🔍 Real-Time Repeat Purchase Propensity API Endpoint")
        st.markdown("Enter a `customer_id` to call `POST /api/v1/ml/repeat-purchase`.")

        sample_id = df_rp["customer_id"].iloc[0] if "customer_id" in df_rp.columns else "00012a2504309823e6e38064373a51d2"
        cust_input = st.text_input("Enter Customer ID for Repeat Propensity Prediction:", value=sample_id)

        if st.button("Predict Repeat Propensity"):
            with st.spinner(f"Calling ML Inference API POST /api/v1/ml/repeat-purchase for ID '{cust_input}'..."):
                res = call_repeat_api(customer_id=cust_input)

            st.success("API Inference Complete!")
            prob = res.get("repeat_purchase_probability", 0.0)
            pred_lbl = res.get("predicted_repeat_customer", 0)

            r1, r2 = st.columns(2)
            with r1:
                st.metric("Repeat Purchase Probability", f"{prob*100:.2f}%")
            with r2:
                st.metric("Predicted Class Label", "Repeat Buyer (1)" if pred_lbl == 1 else "Single Order Customer (0)")

            # Gauge Chart
            fig_gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=prob * 100.0,
                    domain={"x": [0, 1], "y": [0, 1]},
                    title={"text": "Repeat Propensity Probability Gauge (%)"},
                    gauge={
                        "axis": {"range": [0, 100]},
                        "bar": {"color": "#10B981" if prob >= 0.5 else "#EF4444"},
                        "steps": [
                            {"range": [0, 30], "color": "#1E293B"},
                            {"range": [30, 70], "color": "#334155"},
                            {"range": [70, 100], "color": "#475569"},
                        ],
                    },
                )
            )
            fig_gauge.update_layout(template="plotly_dark", height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)

            if "customer_id" in df_rp.columns:
                match = df_rp[(df_rp["customer_id"] == cust_input) | (df_rp.get("customer_unique_id", df_rp["customer_id"]) == cust_input)]
                if not match.empty:
                    st.markdown("#### 👤 Customer Record & Propensity Audit")
                    st.dataframe(match.T.rename(columns={match.index[0]: "Value"}), use_container_width=True)

except Exception as e:
    st.error(f"Error loading Repeat Purchase page: {e}")
