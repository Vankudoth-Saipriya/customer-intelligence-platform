"""
Product Analytics Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.data_provider import get_product_eda

st.set_page_config(page_title="Product Analytics", page_icon="📦", layout="wide")

st.title("📦 Product Analytics")
st.markdown("Category demand, product dimensions, revenue concentration, and freight logistics analysis.")

try:
    with st.spinner("Loading product analysis data..."):
        prod_eda = get_product_eda() or {}

    cat_analysis = prod_eda.get("category_analysis", {})
    rev_cat = cat_analysis.get("revenue_by_category", {})
    orders_cat = cat_analysis.get("order_count_by_category", {})

    dim_analysis = prod_eda.get("dimension_analysis", {})
    weight_dist = dim_analysis.get("weight_distribution", {})
    volume_dist = dim_analysis.get("volume_distribution", {})

    prod_perf = prod_eda.get("product_performance", {})
    freight_analysis = prod_eda.get("freight_analysis", {})
    trans_coverage = prod_eda.get("translation_coverage", {})

    total_prods = prod_eda.get("total_products_analyzed", 32951)
    num_cats = len(rev_cat) if rev_cat else 71
    prods_sales = prod_perf.get("total_products_with_sales", 32951)
    trans_pct = trans_coverage.get("translation_coverage_percentage", 100.0)

    # KPI summary row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Products Analyzed", f"{total_prods:,}")
    with c2:
        st.metric("Total Product Categories", f"{num_cats}")
    with c3:
        st.metric("Products With Sales", f"{prods_sales:,}")
    with c4:
        st.metric("Translation Coverage", f"{trans_pct:.1f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Top Categories by Revenue & Orders
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏆 Top 15 Product Categories by Revenue ($)")
        if rev_cat:
            df_rev_cat = pd.DataFrame(list(rev_cat.items()), columns=["Category", "Revenue"]).head(15)
            fig_rev = px.bar(
                df_rev_cat,
                x="Revenue",
                y="Category",
                orientation="h",
                color="Revenue",
                color_continuous_scale="Blues",
                title="Top 15 Categories by Total Revenue ($)",
            )
            fig_rev.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_rev, use_container_width=True)
        else:
            st.warning("Category revenue data unavailable")

    with col_b:
        st.subheader("🛒 Top 15 Categories by Order Volume")
        if orders_cat:
            df_ord_cat = pd.DataFrame(list(orders_cat.items()), columns=["Category", "Orders"]).head(15)
            fig_ord = px.bar(
                df_ord_cat,
                x="Orders",
                y="Category",
                orientation="h",
                color="Orders",
                color_continuous_scale="Purples",
                title="Top 15 Categories by Order Volume",
            )
            fig_ord.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_ord, use_container_width=True)
        else:
            st.warning("Category order count data unavailable")

    # 2. Product Dimensions Analysis
    st.subheader("📐 Product Weight & Volume Physical Distributions")
    col_c, col_d = st.columns(2)

    with col_c:
        st.write("**Weight Statistics (g)**")
        if weight_dist:
            df_weight = pd.DataFrame([weight_dist])
            st.dataframe(df_weight, use_container_width=True, hide_index=True)
        else:
            st.warning("Weight distribution data unavailable")

    with col_d:
        st.write("**Volume Statistics (cm³)**")
        if volume_dist:
            df_vol = pd.DataFrame([volume_dist])
            st.dataframe(df_vol, use_container_width=True, hide_index=True)
        else:
            st.warning("Volume distribution data unavailable")

    # 3. Freight Analysis & Correlations
    st.subheader("🚚 Freight Logistics Analysis")
    col_e, col_f = st.columns(2)

    weight_corr = freight_analysis.get("freight_vs_weight_correlation", 0.0)
    vol_corr = freight_analysis.get("freight_vs_volume_correlation", 0.0)

    with col_e:
        st.metric("Freight vs Product Weight Correlation", f"{weight_corr:.4f}")
    with col_f:
        st.metric("Freight vs Product Volume Correlation", f"{vol_corr:.4f}")

except Exception as e:
    st.error(f"Error loading Product Analytics: {e}")
