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
        prod_eda = get_product_eda()

    # KPI summary row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Products Analyzed", f"{prod_eda['total_products_analyzed']:,}")
    with c2:
        st.metric("Total Product Categories", len(prod_eda['product_category_analysis']['revenue_by_category']))
    with c3:
        st.metric("Products With Sales", f"{prod_eda['product_performance']['total_products_with_sales']:,}")
    with c4:
        st.metric("Translation Coverage", f"{prod_eda['translation_coverage']['translation_coverage_percentage']:.1f}%")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Top Categories by Revenue & Orders
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏆 Top 15 Product Categories by Revenue ($)")
        rev_cat = prod_eda['product_category_analysis']['revenue_by_category']
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

    with col_b:
        st.subheader("🛒 Top 15 Categories by Order Volume")
        orders_cat = prod_eda['product_category_analysis']['order_count_by_category']
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

    # 2. Product Dimensions Analysis
    st.subheader("📐 Product Weight & Volume Physical Distributions")
    dims = prod_eda.get("product_dimension_analysis", {})
    col_c, col_d = st.columns(2)

    with col_c:
        st.write("**Weight Statistics (g)**")
        df_weight = pd.DataFrame([dims.get("weight_distribution", {})])
        st.dataframe(df_weight, use_container_width=True, hide_index=True)

    with col_d:
        st.write("**Volume Statistics (cm³)**")
        df_vol = pd.DataFrame([dims.get("volume_distribution", {})])
        st.dataframe(df_vol, use_container_width=True, hide_index=True)

    # 3. Freight Analysis & Correlations
    st.subheader("🚚 Freight Logistics Analysis")
    freight = prod_eda.get("freight_analysis", {})
    col_e, col_f = st.columns(2)

    with col_e:
        st.metric("Freight vs Product Weight Correlation", f"{freight.get('freight_vs_weight_correlation', 0):.4f}")
    with col_f:
        st.metric("Freight vs Product Volume Correlation", f"{freight.get('freight_vs_volume_correlation', 0):.4f}")

except Exception as e:
    st.error(f"Error loading Product Analytics: {e}")
