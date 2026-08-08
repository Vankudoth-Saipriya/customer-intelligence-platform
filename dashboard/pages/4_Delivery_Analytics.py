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
        deliv_eda = get_delivery_eda() or {}

    time_info = deliv_eda.get("delivery_time_analysis", {})
    delay_info = deliv_eda.get("delivery_delay_analysis", {})
    op_metrics = deliv_eda.get("operational_metrics", {})
    reg_perf = deliv_eda.get("regional_delivery_performance", {})

    avg_deliv_days = time_info.get("average_actual_delivery_days", time_info.get("delivery_time_stats", {}).get("mean", 12.5))
    sla_pct = op_metrics.get("delivery_sla_achievement_rate_percent", delay_info.get("on_time_delivery_rate_percent", 92.01))
    avg_delay_days = delay_info.get("average_delivery_delay_days", -10.8)
    late_rate_pct = 100.0 - sla_pct

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Average Delivery Days", f"{avg_deliv_days:.1f} days")
    with c2:
        st.metric("Delivery SLA Achievement", f"{sla_pct:.1f}%")
    with c3:
        st.metric("Average Delivery Delay", f"{avg_delay_days:.1f} days")
    with c4:
        st.metric("Late Deliveries Rate", f"{late_rate_pct:.1f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Delivery Days & Delay Distributions
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("⏱️ Regional Delivery Time by State (Avg Days)")
        state_deliv = reg_perf.get("average_delivery_time_by_state", {})
        if state_deliv:
            df_state_deliv = pd.DataFrame(list(state_deliv.items()), columns=["State", "Avg Days"]).sort_values(by="Avg Days")
            fig_days = px.bar(
                df_state_deliv.head(15),
                x="State",
                y="Avg Days",
                color="Avg Days",
                color_continuous_scale="Teal",
                title="Delivery Duration by State (Fastest 15)",
            )
            fig_days.update_layout(template="plotly_dark")
            st.plotly_chart(fig_days, use_container_width=True)
        else:
            st.warning("Regional delivery duration data unavailable")

    with col_b:
        st.subheader("🚨 Delivery Delay Breakdown")
        delay_cats = delay_info.get("delay_categories") or delay_info.get("delay_distribution", {})
        if delay_cats:
            delay_list = [(k, v.get("count", v) if isinstance(v, dict) else v) for k, v in delay_cats.items()]
            df_delay = pd.DataFrame(delay_list, columns=["Delay Status", "Orders"])

            fig_delay = px.pie(
                df_delay,
                names="Delay Status",
                values="Orders",
                hole=0.4,
                title="Early / On-Time vs. Late Delivery Breakdown",
                color_discrete_sequence=["#10B981", "#EF4444"],
            )
            fig_delay.update_layout(template="plotly_dark")
            st.plotly_chart(fig_delay, use_container_width=True)
        else:
            st.warning("Delivery delay breakdown data unavailable")

    # 2. Regional Delivery Speed Comparison (State level)
    st.subheader("🗺️ Regional State Delivery Speed Comparison")
    fastest_list = reg_perf.get("top_20_fastest_states", [])
    slowest_list = reg_perf.get("top_20_slowest_states", [])

    if not fastest_list and state_deliv:
        df_sorted = pd.DataFrame(list(state_deliv.items()), columns=["state", "average_delivery_days"]).sort_values(by="average_delivery_days")
        fastest_list = df_sorted.head(10).to_dict("records")
        slowest_list = df_sorted.tail(10).sort_values(by="average_delivery_days", ascending=False).to_dict("records")

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("🚀 10 Fastest Delivery States")
        if fastest_list:
            df_fast = pd.DataFrame(fastest_list).head(10)
            fig_fast = px.bar(
                df_fast,
                x="average_delivery_days",
                y="state",
                orientation="h",
                color="average_delivery_days",
                color_continuous_scale="Greens",
                title="Top 10 Fastest States (Avg Days)",
            )
            fig_fast.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_fast, use_container_width=True)
        else:
            st.warning("Fastest states data unavailable")

    with col_d:
        st.subheader("🐌 10 Slowest Delivery States")
        if slowest_list:
            df_slow = pd.DataFrame(slowest_list).head(10)
            fig_slow = px.bar(
                df_slow,
                x="average_delivery_days",
                y="state",
                orientation="h",
                color="average_delivery_days",
                color_continuous_scale="Reds",
                title="Top 10 Slowest States (Avg Days)",
            )
            fig_slow.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_slow, use_container_width=True)
        else:
            st.warning("Slowest states data unavailable")

except Exception as e:
    st.error(f"Error loading Delivery Analytics: {e}")
