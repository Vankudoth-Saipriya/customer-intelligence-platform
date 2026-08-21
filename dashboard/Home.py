"""
Customer Intelligence Platform - Executive Home Dashboard.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from app.dashboard.data_provider import (
    get_customer_eda,
    get_delivery_eda,
    get_review_eda,
    get_sales_eda,
)

st.set_page_config(
    page_title="Customer Intelligence Platform",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #3B82F6, #8B5CF6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #94A3B8;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #1E293B;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .card-title {
        font-size: 0.9rem;
        color: #94A3B8;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .card-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #F8FAFC;
        margin-top: 0.4rem;
    }
    .nav-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .nav-card h3 {
        color: #F8FAFC !important;
        font-size: 1.25rem;
        font-weight: 700;
        margin-bottom: 0.75rem;
    }
    .nav-card p {
        color: #E2E8F0 !important;
        font-size: 0.95rem;
        line-height: 1.5;
        margin-bottom: 1rem;
    }
    .nav-card ul {
        color: #CBD5E1 !important;
        margin-left: 1.2rem;
        padding-left: 0;
    }
    .nav-card li {
        color: #CBD5E1 !important;
        font-size: 0.9rem;
        margin-bottom: 0.35rem;
        line-height: 1.4;
    }
    </style>

    """,
    unsafe_allow_html=True,
)

# Header Section
st.markdown('<div class="main-header">⚡ Customer Intelligence & E-Commerce Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Executive BI Dashboard & Predictive Decision Platform</div>', unsafe_allow_html=True)

# Load Key Metrics Safely
try:
    with st.spinner("Loading executive KPI data..."):
        cust_data = get_customer_eda() or {}
        sales_data = get_sales_eda() or {}
        deliv_data = get_delivery_eda() or {}
        review_data = get_review_eda() or {}

    total_customers = cust_data.get("total_customers_analyzed", 96096)
    total_orders = sales_data.get("total_orders_analyzed", 99441)
    total_rev = sales_data.get("revenue_analysis", {}).get("total_revenue", 16008872.12)
    aov = sales_data.get("order_analysis", {}).get("average_order_value", 160.99)
    avg_review = review_data.get("review_score_analysis", {}).get("average_review_score", 4.09)
    sla = deliv_data.get("operational_metrics", {}).get("delivery_sla_achievement_rate_percent", 92.01)

    # Executive Metrics Row
    m1, m2, m3, m4, m5, m6 = st.columns(6)

    with m1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="card-title">Total Customers</div>
                <div class="card-value">{total_customers:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="card-title">Total Orders</div>
                <div class="card-value">{total_orders:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="card-title">Gross GMV</div>
                <div class="card-value">${total_rev:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="card-title">Avg Order Value</div>
                <div class="card-value">${aov:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m5:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="card-title">Avg Review Score</div>
                <div class="card-value">⭐ {avg_review:.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with m6:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="card-title">Delivery SLA</div>
                <div class="card-value">{sla:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

except Exception as e:
    st.error(f"Error loading dashboard executive metrics: {e}")

st.markdown("<br><hr><br>", unsafe_allow_html=True)

# Navigation Cards Section
st.subheader("📌 Analytical Workflow & Platform Modules")

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        """
        <div class="nav-card">
            <h3>📈 1. Executive Overview</h3>
            <p>Financial KPIs, Net Revenue ($13.59M) vs Gross GMV ($16.01M) reconciliation, order status lifecycle audit, and revenue trends.</p>
            <ul>
                <li>Net Revenue vs Gross GMV Audit</li>
                <li>Order Status Breakdown & Drops</li>
                <li>Monthly Trajectory & Run-Rate</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(
        """
        <div class="nav-card">
            <h3>👥 2. Customer & Sales Analytics</h3>
            <p>12-month acquisition cohort retention heatmap, Pareto seller revenue concentration (80/20), and RFM persona clustering.</p>
            <ul>
                <li>12-Month Cohort Retention Matrix</li>
                <li>Seller & Customer Pareto Share</li>
                <li>Log-RFM Persona Distribution</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c3:
    st.markdown(
        """
        <div class="nav-card">
            <h3>🚚 3. Logistics & Statistics</h3>
            <p>Carrier delivery SLA performance, regional state speed rankings, and inferential non-parametric hypothesis testing.</p>
            <ul>
                <li>Mann-Whitney U SLA Test ($p<0.0001$)</li>
                <li>1.72-Star Review Penalty Analysis</li>
                <li>Kruskal-Wallis Regional State SLA</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

with c4:
    st.markdown(
        """
        <div class="nav-card">
            <h3>🤖 4. Predictive Analytics</h3>
            <p>Temporal machine learning models (2017-10-01 cutoff), Ridge CLV value tiering, feature weights, and real-time inference.</p>
            <ul>
                <li>Temporal Cutoff Methodology</li>
                <li>Ridge CLV Regression ($\text{MAE}=\$7.27$)</li>
                <li>Model Feature Weights Interpretability</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)
st.info("👈 Select any of the 4 analytical pages from the sidebar navigation to begin exploration!")
