"""
Sales Analytics Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.data_provider import get_sales_eda

st.set_page_config(page_title="Sales Analytics", page_icon="📈", layout="wide")

st.title("📈 Sales & Revenue Analytics")
st.markdown("Historical sales performance, monthly & quarterly revenue trends, and seasonality patterns.")

try:
    with st.spinner("Loading sales analysis data..."):
        sales_eda = get_sales_eda()

    rev_info = sales_eda['revenue_analysis']
    ord_info = sales_eda['order_analysis']

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Revenue", f"${rev_info['total_revenue']:,.2f}")
    with c2:
        st.metric("Total Orders", f"{ord_info['total_orders']:,}")
    with c3:
        st.metric("Average Order Value", f"${ord_info['average_order_value']:.2f}")
    with c4:
        st.metric("Avg Items Per Order", f"{sales_eda['operational_metrics']['average_items_per_order']:.2f}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Monthly Revenue Trend
    st.subheader("📅 Monthly Revenue Trend")
    monthly_rev = rev_info['revenue_by_month']
    df_monthly = pd.DataFrame(list(monthly_rev.items()), columns=["Month", "Revenue"])
    fig_monthly = px.line(
        df_monthly,
        x="Month",
        y="Revenue",
        markers=True,
        title="Monthly Revenue Trajectory ($)",
    )
    fig_monthly.update_traces(line_color="#10B981", line_width=3)
    fig_monthly.update_layout(template="plotly_dark")
    st.plotly_chart(fig_monthly, use_container_width=True)

    # 2. Quarterly & Weekday Sales
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📊 Quarterly Revenue ($)")
        q_rev = rev_info['revenue_by_quarter']
        df_q = pd.DataFrame(list(q_rev.items()), columns=["Quarter", "Revenue"])
        fig_q = px.bar(
            df_q,
            x="Quarter",
            y="Revenue",
            color="Revenue",
            color_continuous_scale="Viridis",
            title="Quarterly Revenue Breakdown",
        )
        fig_q.update_layout(template="plotly_dark")
        st.plotly_chart(fig_q, use_container_width=True)

    with col_b:
        st.subheader("📆 Orders by Day of Week")
        weekday_orders = ord_info['orders_by_weekday']
        df_w = pd.DataFrame(list(weekday_orders.items()), columns=["Weekday", "Orders"])
        fig_w = px.bar(
            df_w,
            x="Weekday",
            y="Orders",
            color="Orders",
            color_continuous_scale="Plasma",
            title="Orders by Day of Week",
        )
        fig_w.update_layout(template="plotly_dark")
        st.plotly_chart(fig_w, use_container_width=True)

    # 3. Revenue Concentration & Peak Months
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("🔥 Highest Revenue Months")
        high_months = sales_eda['sales_performance']['highest_revenue_months']
        st.dataframe(pd.DataFrame(high_months), use_container_width=True, hide_index=True)

    with col_d:
        st.subheader("⚖️ Revenue Concentration Tiers")
        conc = sales_eda['sales_performance']['revenue_concentration']
        df_conc = pd.DataFrame([
            {"Tier": "Top 1% Customers Revenue Share", "Percentage": f"{conc.get('top_1_percent_revenue_share_pct', 0):.2f}%"},
            {"Tier": "Top 5% Customers Revenue Share", "Percentage": f"{conc.get('top_5_percent_revenue_share_pct', 0):.2f}%"},
            {"Tier": "Top 10% Customers Revenue Share", "Percentage": f"{conc.get('top_10_percent_revenue_share_pct', 0):.2f}%"},
            {"Tier": "Top 20% Customers Revenue Share", "Percentage": f"{conc.get('top_20_percent_revenue_share_pct', 0):.2f}%"},
        ])
        st.dataframe(df_conc, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading Sales Analytics: {e}")
