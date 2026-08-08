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
        pay_eda = get_payment_eda()

    val_info = pay_eda['payment_value_analysis']
    inst_info = pay_eda['installment_analysis']
    biz_info = pay_eda['business_metrics']

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Payment Value", f"${val_info['total_payment_value']:,.2f}")
    with c2:
        st.metric("Average Payment Value", f"${val_info['average_payment_value']:.2f}")
    with c3:
        st.metric("Average Installments", f"{inst_info['average_installment_count']:.2f}")
    with c4:
        st.metric("Installment Revenue Share", f"{biz_info['installment_revenue_contribution_pct']:.1f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Payment Method Breakdown & Revenue Contribution
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("💳 Payment Method Share (%)")
        contrib = biz_info['payment_method_contribution_pct']
        df_contrib = pd.DataFrame(list(contrib.items()), columns=["Payment Method", "Contribution %"])
        fig_pmt = px.pie(
            df_contrib,
            names="Payment Method",
            values="Contribution %",
            hole=0.4,
            title="Revenue Contribution by Payment Method",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        fig_pmt.update_layout(template="plotly_dark")
        st.plotly_chart(fig_pmt, use_container_width=True)

    with col_b:
        st.subheader("💰 Average Payment Value by Method ($)")
        avg_pmt = pay_eda['payment_method_analysis']['average_payment_value_by_payment_method']
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

    # 2. Installments Breakdown
    st.subheader("🔢 Installment Count Distribution")
    inst_dist = inst_info['installment_count_distribution']
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

except Exception as e:
    st.error(f"Error loading Payment Analytics: {e}")
