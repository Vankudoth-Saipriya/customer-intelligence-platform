"""
Delivery Analytics Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.data_provider import get_delivery_eda

st.set_page_config(page_title="Delivery Analytics", page_icon="🚚", layout="wide")

st.title("🚚 Delivery & Logistics Analytics")
st.markdown("Fulfillment SLA performance, carrier delivery delays, and state-level delivery speed comparison.")

try:
    with st.spinner("Loading delivery analysis data..."):
        deliv_eda = get_delivery_eda()

    time_info = deliv_eda['delivery_time_analysis']
    delay_info = deliv_eda['delivery_delay_analysis']
    op_metrics = deliv_eda['operational_metrics']

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Average Delivery Days", f"{time_info['average_delivery_days']:.1f} days")
    with c2:
        st.metric("Delivery SLA Achievement", f"{op_metrics['delivery_sla_achievement_rate']:.1f}%")
    with c3:
        st.metric("Average Delivery Delay", f"{delay_info['average_delivery_delay']:.1f} days")
    with c4:
        st.metric("Late Deliveries Rate", f"{delay_info['percentage_late_deliveries']:.1f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Delivery Days & Delay Distributions
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("⏱️ Delivery Days Distribution")
        dist_days = time_info['delivery_day_distribution']
        df_days = pd.DataFrame(list(dist_days.items()), columns=["Delivery Bucket", "Orders"])
        fig_days = px.bar(
            df_days,
            x="Delivery Bucket",
            y="Orders",
            color="Orders",
            color_continuous_scale="Teal",
            title="Distribution of Order Delivery Duration",
        )
        fig_days.update_layout(template="plotly_dark")
        st.plotly_chart(fig_days, use_container_width=True)

    with col_b:
        st.subheader("🚨 Delivery Delay Distribution")
        dist_delay = delay_info['delay_distribution']
        df_delay = pd.DataFrame(list(dist_delay.items()), columns=["Delay Status", "Orders"])
        fig_delay = px.pie(
            df_delay,
            names="Delay Status",
            values="Orders",
            hole=0.4,
            title="Early / On-Time / Late Delivery Breakdown",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_delay.update_layout(template="plotly_dark")
        st.plotly_chart(fig_delay, use_container_width=True)

    # 2. Regional Delivery Speed Comparison (State level)
    st.subheader("🗺️ Regional State Delivery Speed Comparison")
    reg_perf = deliv_eda['regional_delivery_performance']
    fastest_states = pd.DataFrame(reg_perf['top_20_fastest_states'])
    slowest_states = pd.DataFrame(reg_perf['top_20_slowest_states'])

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("🚀 10 Fastest Delivery States")
        fig_fast = px.bar(
            fastest_states.head(10),
            x="average_delivery_days",
            y="state",
            orientation="h",
            color="average_delivery_days",
            color_continuous_scale="Greens",
            title="Top 10 Fastest States (Avg Days)",
        )
        fig_fast.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_fast, use_container_width=True)

    with col_d:
        st.subheader("🐌 10 Slowest Delivery States")
        fig_slow = px.bar(
            slowest_states.head(10),
            x="average_delivery_days",
            y="state",
            orientation="h",
            color="average_delivery_days",
            color_continuous_scale="Reds",
            title="Top 10 Slowest States (Avg Days)",
        )
        fig_slow.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_slow, use_container_width=True)

except Exception as e:
    st.error(f"Error loading Delivery Analytics: {e}")
