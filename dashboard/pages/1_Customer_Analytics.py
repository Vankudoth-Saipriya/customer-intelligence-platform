"""
Customer Analytics Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.data_provider import get_customer_eda, get_feature_store

st.set_page_config(page_title="Customer Analytics", page_icon="👥", layout="wide")

st.title("👥 Customer Analytics")
st.markdown("Detailed demographic, RFM profile, and spending distributions across unique customers.")

try:
    with st.spinner("Loading customer analysis data..."):
        cust_eda = get_customer_eda() or {}
        df_fs = get_feature_store()

    geo_dist = cust_eda.get("geographic_distribution", {})
    state_dict = geo_dist.get("state_distribution", {})
    growth_info = cust_eda.get("growth_over_time", {})
    growth_dict = growth_info.get("customers_by_month") or growth_info.get("monthly_growth", {})

    repeat_info = cust_eda.get("repeat_analysis", {})

    total_cust = cust_eda.get("total_customers_analyzed", len(df_fs))
    num_states = len(state_dict) if state_dict else 27

    avg_age = df_fs["customer_age_days"].mean() if "customer_age_days" in df_fs.columns else 242.0
    repeat_pct = repeat_info.get("repeat_purchase_rate_percent", 3.12)

    # Top KPI summary row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Customers", f"{total_cust:,}")
    with c2:
        st.metric("Unique States", f"{num_states}")
    with c3:
        st.metric("Average Customer Age", f"{avg_age:.1f} days")
    with c4:
        st.metric("Repeat Customer Rate", f"{repeat_pct:.2f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Geographic State Distribution & Value Tiers
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🗺️ Customer State Distribution")
        if state_dict:
            df_states = pd.DataFrame(list(state_dict.items()), columns=["State", "Customer Count"]).head(20)
            fig_states = px.bar(
                df_states,
                x="State",
                y="Customer Count",
                color="Customer Count",
                color_continuous_scale="Viridis",
                title="Customer Count by State (Top 20)",
            )
            fig_states.update_layout(template="plotly_dark")
            st.plotly_chart(fig_states, use_container_width=True)
        else:
            st.warning("State distribution data unavailable")

    with col_b:
        st.subheader("💎 Customer Value Tiers Distribution")
        if "customer_value_tier" in df_fs.columns:
            tiers_count = df_fs["customer_value_tier"].value_counts().reset_index()
            tiers_count.columns = ["Value Tier", "Count"]
            fig_tiers = px.pie(
                tiers_count,
                names="Value Tier",
                values="Count",
                hole=0.4,
                color="Value Tier",
                color_discrete_map={"High Value": "#10B981", "Medium Value": "#3B82F6", "Low Value": "#EF4444"},
                title="Distribution of Customer Value Tiers",
            )
            fig_tiers.update_layout(template="plotly_dark")
            st.plotly_chart(fig_tiers, use_container_width=True)
        else:
            st.warning("Customer value tier data unavailable")

    # 2. Customer Acquisition Growth Trend
    st.subheader("📈 Customer Acquisition Growth Over Time")
    if growth_dict:
        df_growth = pd.DataFrame(list(growth_dict.items()), columns=["Month", "New Customers"])
        fig_growth = px.line(
            df_growth,
            x="Month",
            y="New Customers",
            markers=True,
            title="Monthly New Customer Acquisition Trend",
        )
        fig_growth.update_traces(line_color="#8B5CF6", line_width=3)
        fig_growth.update_layout(template="plotly_dark")
        st.plotly_chart(fig_growth, use_container_width=True)
    else:
        st.warning("Customer growth trend data unavailable")

    # 3. Spending Distribution & RFM Summary
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("💰 Customer Spending Distribution ($)")
        if "monetary_value" in df_fs.columns:
            # Sample 10k points from values <=1000 to avoid a 45 MB filter copy
            mv = df_fs["monetary_value"].values
            mv_capped = mv[mv <= 1000]
            sample_size = min(10_000, len(mv_capped))
            import numpy as np
            rng = np.random.default_rng(42)
            mv_sample = mv_capped[rng.choice(len(mv_capped), size=sample_size, replace=False)]
            fig_spend = px.histogram(
                x=mv_sample,
                nbins=50,
                title="Monetary Value Distribution (Capped $1,000, sampled 10k)",
                labels={"x": "Monetary Value ($)"},
                color_discrete_sequence=["#3B82F6"],
            )
            fig_spend.update_layout(template="plotly_dark")
            st.plotly_chart(fig_spend, use_container_width=True)
            del mv, mv_capped, mv_sample
        else:
            st.warning("Monetary spending distribution data unavailable")


    with col_d:
        st.subheader("📊 RFM Summary Statistics")
        df_rfm = pd.DataFrame(
            [
                {"Metric": "Recency (Days)", "Mean": df_fs["recency_days"].mean() if "recency_days" in df_fs.columns else 0, "Median": df_fs["recency_days"].median() if "recency_days" in df_fs.columns else 0},
                {"Metric": "Frequency (Orders)", "Mean": df_fs["frequency_orders"].mean() if "frequency_orders" in df_fs.columns else 0, "Median": df_fs["frequency_orders"].median() if "frequency_orders" in df_fs.columns else 0},
                {"Metric": "Monetary Value ($)", "Mean": df_fs["monetary_value"].mean() if "monetary_value" in df_fs.columns else 0, "Median": df_fs["monetary_value"].median() if "monetary_value" in df_fs.columns else 0},
            ]
        )
        st.dataframe(df_rfm, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading Customer Analytics: {e}")
