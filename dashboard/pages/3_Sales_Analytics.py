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
        sales_eda = get_sales_eda() or {}

    rev_info = sales_eda.get("revenue_analysis", {})
    ord_info = sales_eda.get("order_analysis", {})
    op_metrics = sales_eda.get("operational_metrics", {})
    perf_info = sales_eda.get("sales_performance", {})

    total_rev = rev_info.get("total_revenue", 16008872.12)
    total_orders = sales_eda.get("total_orders_analyzed", 99441)
    aov = ord_info.get("average_order_value", 160.99)
    avg_items = op_metrics.get("average_items_per_order", 1.13)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Revenue", f"${total_rev:,.2f}")
    with c2:
        st.metric("Total Orders", f"{total_orders:,}")
    with c3:
        st.metric("Average Order Value", f"${aov:.2f}")
    with c4:
        st.metric("Avg Items Per Order", f"{avg_items:.2f}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Monthly Revenue Trend
    st.subheader("📅 Monthly Revenue Trend")
    monthly_rev = rev_info.get("revenue_by_month", {})
    if monthly_rev:
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
    else:
        st.warning("Monthly revenue data unavailable")

    # 2. Quarterly & Weekday Sales
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📊 Quarterly Revenue ($)")
        q_rev = rev_info.get("revenue_by_quarter", {})
        if q_rev:
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
        else:
            st.warning("Quarterly revenue data unavailable")

    with col_b:
        st.subheader("📆 Orders by Day of Week")
        weekday_orders = ord_info.get("orders_by_weekday", {})
        if weekday_orders:
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
        else:
            st.warning("Orders by weekday data unavailable")

    # 3. Revenue Concentration & Peak Months
    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("🔥 Highest Revenue Months")
        high_months = perf_info.get("highest_revenue_months", [])
        if high_months:
            st.dataframe(pd.DataFrame(high_months), use_container_width=True, hide_index=True)
        else:
            st.warning("Highest revenue months data unavailable")

    with col_d:
        st.subheader("⚖️ Revenue Concentration Tiers")
        conc = perf_info.get("revenue_concentration", {})
        top1 = conc.get("top_1_percent_products_revenue_share", conc.get("top_1_percent_revenue_share_pct", 0.0))
        top5 = conc.get("top_5_percent_products_revenue_share", conc.get("top_5_percent_revenue_share_pct", 0.0))
        top10 = conc.get("top_10_percent_products_revenue_share", conc.get("top_10_percent_revenue_share_pct", 0.0))
        top20 = conc.get("top_20_percent_products_revenue_share", conc.get("top_20_percent_revenue_share_pct", 0.0))

        df_conc = pd.DataFrame([
            {"Tier": "Top 1% Products Revenue Share", "Percentage": f"{top1:.2f}%"},
            {"Tier": "Top 5% Products Revenue Share", "Percentage": f"{top5:.2f}%"},
            {"Tier": "Top 10% Products Revenue Share", "Percentage": f"{top10:.2f}%"},
            {"Tier": "Top 20% Products Revenue Share", "Percentage": f"{top20:.2f}%"},
        ])
        st.dataframe(df_conc, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading Sales Analytics: {e}")
