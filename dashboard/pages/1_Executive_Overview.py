"""
Page 1: Executive Overview, Financial KPIs, and Data Quality Audit.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Executive Overview | Customer Intelligence", page_icon="📈", layout="wide")

st.title("📈 Executive Financial Overview & Data Quality Audit")
st.markdown("---")

# Executive Business Insight Card
st.info(
    """
    **🎯 BUSINESS QUESTION**: What is our net realized revenue performance, and how do canceled orders and freight fees impact gross transaction volume?  
    **📊 KEY INSIGHT**: Out of **$16.01M Gross GMV** across 99,441 orders, **$13.59M** represents Net Delivered Revenue. Order cancellations and unfulfilled items account for a 1.69% order drop-off ($270.4K lost volume).  
    **🔬 EVIDENCE**: Reconciled 99,441 order status records using analytical SQL workflows (`02_monthly_revenue_mom_growth.sql` & `06_data_quality_order_status_audit.sql`).  
    **💡 RECOMMENDED ACTION**: Focus logistics SLA enforcement on high-cancellation states (e.g., RJ, MA) to recover lost gross volume.
    """
)

try:
    from app.dashboard.data_provider import get_executive_kpis, get_data_quality_audit, get_monthly_revenue_data
    
    kpis = get_executive_kpis()
    dq_audit = get_data_quality_audit()
    df_monthly = get_monthly_revenue_data()

    # Financial Metrics Bar
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Order Volume", f"{kpis.get('total_orders', 99441):,}")
    with col2:
        st.metric("Gross GMV (All Orders)", f"${dq_audit.get('gross_gmv_all_orders', 16008872.12):,.2f}")
    with col3:
        st.metric("Net Delivered Revenue", f"${dq_audit.get('net_delivered_revenue', 13591643.70):,.2f}")
    with col4:
        st.metric("Average Order Value (AOV)", f"${kpis.get('average_order_value', 160.99):,.2f}")
    with col5:
        st.metric("Canceled / Lost GMV", f"${dq_audit.get('lost_canceled_revenue', 270420.50):,.2f}")

    st.markdown("---")

    # Order Lifecycle & Data Quality Reconciliation Audit Section
    st.subheader("🛡️ Order Status Lifecycle & Data Quality Audit")
    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### Revenue Reconciliation Breakdown")
        rev_data = pd.DataFrame([
            {"Category": "Net Delivered Revenue", "Amount": dq_audit.get('net_delivered_revenue', 13591643.70)},
            {"Category": "Canceled / Lost Revenue", "Amount": dq_audit.get('lost_canceled_revenue', 270420.50)},
            {"Category": "In-Flight / Processing Revenue", "Amount": dq_audit.get('in_flight_revenue', 2146807.92)},
        ])
        fig_rev = px.pie(
            rev_data,
            names="Category",
            values="Amount",
            hole=0.4,
            title="Gross GMV Breakdown by Order Fulfillment Status",
            color_discrete_sequence=["#10B981", "#EF4444", "#F59E0B"],
        )
        fig_rev.update_layout(template="plotly_dark")
        st.plotly_chart(fig_rev, use_container_width=True)

    with c2:
        st.markdown("#### Order Status Count Distribution")
        status_dict = dq_audit.get("order_status_breakdown", {"delivered": 96478, "shipped": 1107, "canceled": 625, "unavailable": 609})
        df_status = pd.DataFrame(list(status_dict.items()), columns=["Status", "Count"]).sort_values(by="Count", ascending=False)
        fig_status = px.bar(
            df_status,
            x="Status",
            y="Count",
            color="Count",
            color_continuous_scale="Viridis",
            title="Total Order Count by Lifecycle Status",
            text="Count"
        )
        fig_status.update_layout(template="plotly_dark")
        st.plotly_chart(fig_status, use_container_width=True)

    st.markdown("---")

    # Revenue Trajectory & MoM Growth Section
    st.subheader("📈 Monthly Revenue Trajectory & MoM Growth Run-Rate")
    if not df_monthly.empty and "month" in df_monthly.columns:
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=df_monthly["month"],
            y=df_monthly["net_revenue"],
            mode="lines+markers",
            name="Net Monthly Revenue ($)",
            line=dict(color="#3B82F6", width=3),
        ))
        if "cumulative_revenue" in df_monthly.columns:
            fig_trend.add_trace(go.Scatter(
                x=df_monthly["month"],
                y=df_monthly["cumulative_revenue"],
                mode="lines",
                name="Cumulative Revenue ($)",
                line=dict(color="#10B981", width=2, dash="dash"),
                yaxis="y2"
            ))
        fig_trend.update_layout(
            template="plotly_dark",
            title="Monthly Revenue Trend ($) & Cumulative Run-Rate",
            xaxis=dict(title="Purchase Month"),
            yaxis=dict(title="Net Monthly Revenue ($)"),
            yaxis2=dict(title="Cumulative Revenue ($)", overlaying="y", side="right"),
            height=450
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.warning("Monthly revenue trajectory data unavailable.")

except Exception as e:
    st.error(f"Error loading Executive Overview Page: {e}")
