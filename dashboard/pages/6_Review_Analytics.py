"""
Review Analytics Streamlit Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.data_provider import get_review_eda

st.set_page_config(page_title="Review Analytics", page_icon="⭐", layout="wide")

st.title("⭐ Review & Satisfaction Analytics")
st.markdown("Customer rating distributions, review text sentiment metrics, delivery time impact, and category ratings.")

try:
    with st.spinner("Loading review analysis data..."):
        rev_eda = get_review_eda()

    score_info = rev_eda['review_score_analysis']
    op_metrics = rev_eda['operational_metrics']
    biz_info = rev_eda['business_insights']

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Reviews Analyzed", f"{rev_eda['total_reviews_analyzed']:,}")
    with c2:
        st.metric("Average Rating Score", f"⭐ {score_info['average_review_score']:.2f} / 5.0")
    with c3:
        st.metric("Positive Review Rate (>=4⭐)", f"{op_metrics['positive_review_percentage']:.1f}%")
    with c4:
        st.metric("Review Score vs Delay Corr", f"{biz_info['review_score_vs_delivery_delay_correlation']:.4f}")

    st.markdown("<hr>", unsafe_allow_html=True)

    # 1. Rating Distribution & Rating Trend over Time
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📊 Review Rating Score Distribution (1-5 Stars)")
        score_dist = score_info['review_score_distribution']
        df_score = pd.DataFrame(list(score_dist.items()), columns=["Rating", "Reviews"])
        fig_score = px.bar(
            df_score,
            x="Rating",
            y="Reviews",
            color="Rating",
            color_discrete_map={"5": "#10B981", "4": "#3B82F6", "3": "#F59E0B", "2": "#F97316", "1": "#EF4444"},
            title="Distribution of Star Ratings",
        )
        fig_score.update_layout(template="plotly_dark")
        st.plotly_chart(fig_score, use_container_width=True)

    with col_b:
        st.subheader("📈 Monthly Rating Score Trend")
        trend = score_info['rating_trend_over_time']
        trend_list = [{"Month": k, "Average Score": v["average_score"]} for k, v in trend.items()]
        df_trend = pd.DataFrame(trend_list)
        fig_trend = px.line(
            df_trend,
            x="Month",
            y="Average Score",
            markers=True,
            title="Average Rating Score Over Time",
        )
        fig_trend.update_traces(line_color="#F59E0B", line_width=3)
        fig_trend.update_layout(template="plotly_dark", yaxis_range=[1.0, 5.0])
        st.plotly_chart(fig_trend, use_container_width=True)

    # 2. Delivery vs Rating & Top/Bottom Rated Categories
    st.subheader("🚚 Delivery Duration Bucket vs. Average Review Score")
    deliv_buckets = rev_eda['customer_satisfaction']['average_review_score_by_delivery_time_bucket']
    df_deliv_buckets = pd.DataFrame(list(deliv_buckets.items()), columns=["Delivery Time Bucket", "Avg Score"])
    fig_deliv_score = px.bar(
        df_deliv_buckets,
        x="Delivery Time Bucket",
        y="Avg Score",
        color="Avg Score",
        color_continuous_scale="RdYlGn",
        title="Impact of Delivery Speed on Customer Satisfaction",
    )
    fig_deliv_score.update_layout(template="plotly_dark", yaxis_range=[1.0, 5.0])
    st.plotly_chart(fig_deliv_score, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("🌟 Highest Rated Product Categories")
        st.dataframe(pd.DataFrame(biz_info['categories_with_highest_ratings']), use_container_width=True, hide_index=True)

    with col_d:
        st.subheader("⚠️ Lowest Rated Product Categories")
        st.dataframe(pd.DataFrame(biz_info['categories_with_lowest_ratings']), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading Review Analytics: {e}")
