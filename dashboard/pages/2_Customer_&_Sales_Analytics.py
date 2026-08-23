"""
Page 2: Customer & Sales Analytics (Cohorts, Pareto Revenue, and Segmentation).
"""

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Customer & Sales Analytics | CIP", page_icon="👥", layout="wide")

st.title("👥 Customer & Sales Analytics: Cohorts, Pareto & Segmentation")
st.markdown("---")

# Executive Business Insight Card
st.info(
    """
    **🎯 BUSINESS QUESTION**: Do acquired customers return to place repeat orders, and how concentrated is marketplace revenue among top sellers?
    **📊 KEY INSIGHT**: Across 96,096 unique customers, **3.12%** are overall lifetime repeat buyers (2,997 customers). Monthly acquisition cohorts exhibit an **average Month-1 cohort retention of 0.50%** (median: 0.50%, peak: 0.72%). Seller revenue follows an **80/20 Pareto distribution** (top 20% sellers generate 84.5% of revenue).
    **🔬 EVIDENCE**: Analyzed 96,096 customer profiles and 3,095 sellers using `03_cohort_retention_matrix.sql` & `04_seller_revenue_pareto.sql`.
    **💡 RECOMMENDED ACTION**: Focus post-purchase retention sequences on single-order buyers while prioritizing VIP seller support for the top 20% merchant cohort.
    """
)

try:
    from app.dashboard.data_provider import get_cohort_retention_data, get_pareto_data, get_customer_segmentation_data

    # Section 1: 12-Month Cohort Retention Heatmap
    st.subheader("🗓️ Monthly Customer Acquisition Cohort Retention Matrix")
    cohort_df, retention_df = get_cohort_retention_data()

    if not retention_df.empty:
        # Display Plotly Heatmap
        display_retention = retention_df.iloc[:15, :13]  # Show top 15 cohorts across 12 months
        fig_cohort = px.imshow(
            display_retention,
            labels=dict(x="Months Since First Order (t_i)", y="Acquisition Cohort (t_0)", color="Retention (%)"),
            x=[f"Month {c}" for c in display_retention.columns],
            y=[str(r) for r in display_retention.index],
            color_continuous_scale="Purples",
            text_auto=".1f",
            aspect="auto",
            title="Monthly Cohort Retention Heatmap (% Active Customers)",
        )
        fig_cohort.update_layout(template="plotly_dark", height=450)
        st.plotly_chart(fig_cohort, use_container_width=True)
        st.caption("🔍 **Cohort Retention Finding**: Month-1 retention averages **0.50%** across monthly cohorts (reflecting a **3.12%** overall lifetime repeat buyer rate).")
    else:
        st.warning("Cohort retention data unavailable.")

    st.markdown("---")

    # Section 2: Seller & Customer Pareto Concentration
    st.subheader("📊 Seller Revenue Pareto Concentration (80/20 Rule)")
    c1, c2 = st.columns([1, 1])

    pareto_data = get_pareto_data()
    seller_pareto = pareto_data.get("seller_pareto", pd.DataFrame())
    cust_pareto = pareto_data.get("customer_pareto", pd.DataFrame())

    with c1:
        st.markdown("#### Seller Cumulative Revenue Concentration")
        if not seller_pareto.empty:
            fig_seller_p = px.bar(
                seller_pareto,
                x="seller_percentile",
                y="cumulative_revenue_pct",
                color="cumulative_revenue_pct",
                color_continuous_scale="Viridis",
                title="Seller Revenue Share by Percentile Tier",
                labels={"seller_percentile": "Seller Percentile Tier", "cumulative_revenue_pct": "Cumulative Revenue (%)"},
                text="cumulative_revenue_pct"
            )
            fig_seller_p.update_layout(template="plotly_dark")
            st.plotly_chart(fig_seller_p, use_container_width=True)
            st.caption("💡 Top 10% sellers = **67.49%** revenue; Top 20% sellers = **82.69%** revenue.")
        else:
            st.warning("Seller Pareto data unavailable.")

    with c2:
        st.markdown("#### Customer Cumulative Revenue Concentration")
        if not cust_pareto.empty:
            fig_cust_p = px.bar(
                cust_pareto,
                x="customer_percentile",
                y="cumulative_revenue_pct",
                color="cumulative_revenue_pct",
                color_continuous_scale="Cividis",
                title="Customer Revenue Share by Percentile Tier",
                labels={"customer_percentile": "Customer Percentile Tier", "cumulative_revenue_pct": "Cumulative Revenue (%)"},
                text="cumulative_revenue_pct"
            )
            fig_cust_p.update_layout(template="plotly_dark")
            st.plotly_chart(fig_cust_p, use_container_width=True)
            st.caption("💡 Top 10% customers = **41.37%** revenue; Top 20% customers = **56.94%** revenue.")
        else:
            st.warning("Customer Pareto data unavailable.")

    st.markdown("---")

    # Section 3: Log-RFM Customer Segmentation Summary
    st.subheader("🎯 Customer RFM Persona Breakdown (KMeans K=4)")
    df_seg = get_customer_segmentation_data()

    if not df_seg.empty and "segment_name" in df_seg.columns:
        seg_counts = df_seg["segment_name"].value_counts().reset_index()
        seg_counts.columns = ["Persona", "Customer Count"]
        
        fig_seg = px.pie(
            seg_counts,
            names="Persona",
            values="Customer Count",
            hole=0.4,
            title="Customer Persona Distribution (Log-RFM Clustering)",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_seg.update_layout(template="plotly_dark")
        st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.warning("Segmentation data unavailable.")

except Exception as e:
    st.error(f"Error loading Customer & Sales Analytics Page: {e}")
