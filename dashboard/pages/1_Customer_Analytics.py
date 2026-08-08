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
import plotly.graph_objects as go
import streamlit as st

from app.dashboard.data_provider import get_customer_eda, get_feature_store

st.set_page_config(page_title="Customer Analytics", page_icon="👥", layout="wide")

st.title("👥 Customer Analytics")
st.markdown("Detailed demographic, RFM profile, and spending distributions across unique customers.")

try:
    with st.spinner("Loading customer analysis data..."):
        cust_eda = get_customer_eda()
        df_fs = get_feature_store()

    # Top KPI summary row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Customers", f"{cust_eda['total_customers_analyzed']:,}")
    with c2:
        st.metric("Unique States", len(cust_eda['geographic_distribution']['top_20_states']))
    with c3:
        st.metric("Average Customer Age", f"{df_fs['customer_age_days'].mean():.1f} days")
    with c4:
        st.metric("Repeat Customers", f"{(df_fs['frequency_orders'] > 1).sum():,} ({(df_fs['frequency_orders'] > 1).mean()*100:.2f}%)")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Geographic State Distribution & Value Tiers
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🗺️ Top 20 Customer States")
        states_dict = cust_eda['geographic_distribution']['top_20_states']
        df_states = pd.DataFrame(list(states_dict.items()), columns=["State", "Customer Count"])
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

    with col_b:
        st.subheader("💎 Customer Value Tiers Distribution")
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

    # 2. Customer Acquisition Growth Trend
    st.subheader("📈 Customer Acquisition Growth Over Time")
    growth_dict = cust_eda['customer_growth']['monthly_new_customers']
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

    # 3. Spending Distribution & RFM Summary
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("💰 Customer Spending Distribution ($)")
        fig_spend = px.histogram(
            df_fs[df_fs["monetary_value"] <= 1000],
            x="monetary_value",
            nbins=50,
            title="Monetary Value Distribution (Capped at $1,000 for visibility)",
            labels={"monetary_value": "Monetary Value ($)"},
            color_discrete_sequence=["#3B82F6"],
        )
        fig_spend.update_layout(template="plotly_dark")
        st.plotly_chart(fig_spend, use_container_width=True)

    with col_d:
        st.subheader("📊 RFM Summary Statistics")
        rfm_stats = cust_eda.get("rfm_analysis", {})
        df_rfm = pd.DataFrame(
            [
                {"Metric": "Recency (Days)", "Mean": rfm_stats.get("recency_days_mean"), "Median": rfm_stats.get("recency_days_median"), "Max": rfm_stats.get("recency_days_max")},
                {"Metric": "Frequency (Orders)", "Mean": rfm_stats.get("frequency_orders_mean"), "Median": rfm_stats.get("frequency_orders_median"), "Max": rfm_stats.get("frequency_orders_max")},
                {"Metric": "Monetary Value ($)", "Mean": rfm_stats.get("monetary_value_mean"), "Median": rfm_stats.get("monetary_value_median"), "Max": rfm_stats.get("monetary_value_max")},
            ]
        )
        st.dataframe(df_rfm, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading Customer Analytics: {e}")
