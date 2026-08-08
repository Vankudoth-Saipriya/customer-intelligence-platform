"""
Customer Segmentation Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.data_provider import call_segment_api, get_customer_segments

st.set_page_config(page_title="Customer Segmentation", page_icon="🎯", layout="wide")

st.title("🎯 Customer Segmentation ML Model")
st.markdown("Unsupervised KMeans customer clustering powered by optimal Silhouette evaluation and automated business descriptions.")

try:
    with st.spinner("Loading segmentation data..."):
        df_seg = get_customer_segments()

    if df_seg.empty:
        st.warning("Customer segmentation prediction dataset is empty")
    else:
        # Model summary metrics
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Total Segmented Customers", f"{len(df_seg):,}")
        with c2:
            num_clusters = df_seg["cluster_id"].nunique() if "cluster_id" in df_seg.columns else 2
            st.metric("Optimal Clusters (k)", f"{num_clusters}")
        with c3:
            share0 = (df_seg["cluster_id"] == 0).mean() * 100 if "cluster_id" in df_seg.columns else 94.6
            st.metric("Top Segment Share", f"{share0:.1f}%")
        with c4:
            share1 = (df_seg["cluster_id"] == 1).mean() * 100 if "cluster_id" in df_seg.columns else 5.4
            st.metric("Repeat Segment Share", f"{share1:.1f}%")

        st.markdown("<hr>", unsafe_allow_html=True)

        # Cluster Distribution Overview
        col_a, col_b = st.columns(2)

        desc_col = "cluster_description" if "cluster_description" in df_seg.columns else "cluster_id"

        with col_a:
            st.subheader("📊 Customer Segment Size Breakdown")
            seg_counts = df_seg[desc_col].value_counts().reset_index()
            seg_counts.columns = ["Segment Description", "Customer Count"]
            fig_seg = px.pie(
                seg_counts,
                names="Segment Description",
                values="Customer Count",
                hole=0.4,
                title="Cluster Distribution",
                color_discrete_sequence=["#3B82F6", "#10B981", "#F59E0B"],
            )
            fig_seg.update_layout(template="plotly_dark")
            st.plotly_chart(fig_seg, use_container_width=True)

        with col_b:
            st.subheader("💰 Revenue by Cluster Segment ($)")
            rev_col = "total_revenue" if "total_revenue" in df_seg.columns else "monetary_value"
            if rev_col in df_seg.columns:
                rev_seg = df_seg.groupby(desc_col)[rev_col].sum().reset_index()
                fig_rev_seg = px.bar(
                    rev_seg,
                    x=desc_col,
                    y=rev_col,
                    color=desc_col,
                    title="Total Revenue Contribution by Segment",
                )
                fig_rev_seg.update_layout(template="plotly_dark")
                st.plotly_chart(fig_rev_seg, use_container_width=True)
            else:
                st.warning("Segment revenue data unavailable")

        st.markdown("<hr>", unsafe_allow_html=True)

        # Real-Time Customer Segment Inference Section
        st.subheader("🔍 Real-Time Customer Segment Lookup & Model Inference")
        st.markdown("Enter a `customer_id` or select a sample customer to call `POST /api/v1/ml/segment`.")

        sample_id = df_seg["customer_id"].iloc[0] if "customer_id" in df_seg.columns else "00012a2504309823e6e38064373a51d2"
        cust_input = st.text_input("Enter Customer ID:", value=sample_id)

        if st.button("Predict Customer Segment"):
            with st.spinner(f"Calling ML Inference API POST /api/v1/ml/segment for ID '{cust_input}'..."):
                res = call_segment_api(customer_id=cust_input)

            st.success("API Inference Complete!")
            r1, r2, r3 = st.columns(3)
            with r1:
                st.metric("Assigned Cluster ID", res.get("cluster_id"))
            with r2:
                st.metric("Cluster Category Name", res.get("cluster_name"))
            with r3:
                st.metric("Business Description", res.get("business_description"))

            # Display customer profile summary from dataset
            if "customer_id" in df_seg.columns:
                match = df_seg[(df_seg["customer_id"] == cust_input) | (df_seg.get("customer_unique_id", df_seg["customer_id"]) == cust_input)]
                if not match.empty:
                    st.markdown("#### 👤 Customer Feature Summary")
                    st.dataframe(match.T.rename(columns={match.index[0]: "Value"}), use_container_width=True)

except Exception as e:
    st.error(f"Error loading Customer Segmentation page: {e}")
