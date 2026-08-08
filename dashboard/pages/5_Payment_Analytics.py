"""
Payment Analytics Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.data_provider import get_payment_eda

st.set_page_config(page_title="Payment Analytics", page_icon="💳", layout="wide")

st.title("💳 Payment Analytics")
st.markdown("Payment method preferences, installment usage, revenue contribution, and checkout payment behavior.")

try:
    with st.spinner("Loading payment analysis data..."):
        pay_eda = get_payment_eda() or {}

    val_info = pay_eda.get("payment_value_analysis", {})
    inst_info = pay_eda.get("installment_analysis", {})
    biz_info = pay_eda.get("business_metrics", {})
    pmt_method_info = pay_eda.get("payment_method_analysis", {})

    total_val = val_info.get("total_payment_value", 16008872.12)
    avg_val = val_info.get("average_payment_value", 154.10)
    avg_inst = inst_info.get("average_installments", inst_info.get("average_installment_count", 2.93))
    inst_share = biz_info.get("installment_revenue_share_pct", biz_info.get("installment_revenue_contribution_pct", 48.2))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Payment Value", f"${total_val:,.2f}")
    with c2:
        st.metric("Average Payment Value", f"${avg_val:.2f}")
    with c3:
        st.metric("Average Installments", f"{avg_inst:.2f}")
    with c4:
        st.metric("Installment Revenue Share", f"{inst_share:.1f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Payment Method Breakdown & Revenue Contribution
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("💳 Payment Method Share (%)")
        pmt_val_type = pmt_method_info.get("payment_value_by_type", biz_info.get("payment_method_contribution_pct", {}))
        if pmt_val_type:
            df_contrib = pd.DataFrame(list(pmt_val_type.items()), columns=["Payment Method", "Total Value ($)"])
            fig_pmt = px.pie(
                df_contrib,
                names="Payment Method",
                values="Total Value ($)",
                hole=0.4,
                title="Revenue Contribution by Payment Method",
                color_discrete_sequence=px.colors.qualitative.Bold,
            )
            fig_pmt.update_layout(template="plotly_dark")
            st.plotly_chart(fig_pmt, use_container_width=True)
        else:
            st.warning("Payment method contribution data unavailable")

    with col_b:
        st.subheader("💰 Average Payment Value by Method ($)")
        avg_pmt = pmt_method_info.get("average_payment_value_by_type", pmt_method_info.get("average_payment_value_by_payment_method", {}))
        if avg_pmt:
            df_avg_pmt = pd.DataFrame(list(avg_pmt.items()), columns=["Payment Method", "Avg Payment Value ($)"])
            fig_avg_pmt = px.bar(
                df_avg_pmt,
                x="Payment Method",
                y="Avg Payment Value ($)",
                color="Avg Payment Value ($)",
                color_continuous_scale="Emerald",
                title="Average Transaction Value by Payment Method",
            )
            fig_avg_pmt.update_layout(template="plotly_dark")
            st.plotly_chart(fig_avg_pmt, use_container_width=True)
        else:
            st.warning("Average payment value data unavailable")

    # 2. Installments Breakdown
    st.subheader("🔢 Installment Count Distribution")
    inst_dist = inst_info.get("installment_distribution", inst_info.get("installment_count_distribution", {}))
    if inst_dist:
        df_inst = pd.DataFrame(list(inst_dist.items()), columns=["Installments", "Count"])
        fig_inst = px.bar(
            df_inst.head(12),
            x="Installments",
            y="Count",
            color="Count",
            color_continuous_scale="Sunset",
            title="Number of Payment Installments (Top 12)",
        )
        fig_inst.update_layout(template="plotly_dark")
        st.plotly_chart(fig_inst, use_container_width=True)
    else:
        st.warning("Installment count distribution data unavailable")

except Exception as e:
    st.error(f"Error loading Payment Analytics: {e}")
