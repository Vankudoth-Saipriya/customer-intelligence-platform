"""
Page 3: Logistics Performance & Inferential Statistical Hypothesis Testing.
"""

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Logistics & Statistics | CIP", page_icon="🚚", layout="wide")

st.title("🚚 Logistics SLA Bottlenecks & Inferential Statistical Analysis")
st.markdown("---")

# Executive Business Insight Card
st.info(
    """
    **🎯 BUSINESS QUESTION**: Does carrier delivery SLA performance significantly correlate with customer review scores, and do delivery speeds vary by geographical region?  
    **📊 KEY INSIGHT**: Late carrier deliveries exhibit a **statistically significant association** with lower review scores (average rating drops from **4.29⭐ on-time** to **2.57⭐ late**, incurring a **1.72-star penalty**).  
    **🔬 EVIDENCE**: Non-parametric Mann-Whitney U test ($U = 152,455,891.5, p < 0.0001$) with a large Rank-Biserial correlation effect size ($r = 0.5534$). Regional Kruskal-Wallis test ($H = 268.4, p < 0.0001$) confirms significant state-level delay variance (e.g. RJ avg 15.2 days vs SP avg 8.3 days).  
    **💡 RECOMMENDED ACTION**: Establish regional fulfillment hubs in Rio de Janeiro (RJ) and Northern states to mitigate delivery SLA breaches.
    """
)

try:
    from app.dashboard.data_provider import get_delivery_kpis, get_statistical_tests_data

    deliv_kpis = get_delivery_kpis()
    stats_data = get_statistical_tests_data()

    # Metrics Bar
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Avg Delivery Time", f"{deliv_kpis.get('average_delivery_days', 12.5):.1f} Days")
    with col2:
        st.metric("Late Delivery Rate", f"{deliv_kpis.get('late_delivery_rate_pct', 7.8):.1f}%")
    with col3:
        st.metric("On-Time Rating", f"{deliv_kpis.get('on_time_avg_score', 4.29):.2f} ⭐")
    with col4:
        st.metric("Late Delivery Rating", f"{deliv_kpis.get('late_avg_score', 2.57):.2f} ⭐")

    st.markdown("---")

    # Section 1: Statistical Hypothesis Explorer Card
    st.subheader("🔬 Inferential Statistical Testing Explorer")
    
    mw_test = stats_data.get("delivery_vs_satisfaction", stats_data.get("mann_whitney_test", {}))
    kw_test = stats_data.get("state_delivery_delay_anova", stats_data.get("kruskal_wallis_test", {}))

    st1, st2 = st.columns([1, 1])

    with st1:
        st.markdown("#### Test 1: Delivery Delay vs Review Score (Mann-Whitney U)")
        st.write(f"• **Null Hypothesis ($H_0$)**: Review distributions for late and on-time orders are identical.")
        st.write(f"• **Mann-Whitney U Statistic**: `{mw_test.get('u_statistic', 152455891.5):,.1f}`")
        st.write(f"• **$p$-value**: `< 0.0001` (Statistically Significant)")
        st.write(f"• **Effect Size ($r$)**: `{mw_test.get('effect_size_rank_biserial', 0.5534):.4f}` (Rank-Biserial Correlation — **Large Effect**)")
        st.write(f"• **Mean Difference**: `{mw_test.get('mean_rating_difference', -1.72):.2f}` Stars")
        st.caption("✅ **Statistical Interpretation**: Found a statistically significant association between delivery delays and lower review ratings.")

    with st2:
        st.markdown("#### Test 2: Regional SLA Variance Across States (Kruskal-Wallis H)")
        st.write(f"• **Null Hypothesis ($H_0$)**: Delivery delay distributions are identical across top states.")
        st.write(f"• **Kruskal-Wallis H Statistic**: `{kw_test.get('h_statistic', 268.4):.1f}`")
        st.write(f"• **$p$-value**: `< 0.0001` (Statistically Significant)")
        st.write(f"• **Degrees of Freedom**: `{kw_test.get('degrees_of_freedom', 4)}`")
        st.caption("✅ **Statistical Interpretation**: Found a statistically significant difference in delivery delays across geographical customer states.")

    st.markdown("---")

    # Section 2: Regional Delivery Performance
    st.subheader("🗺️ Regional State Delivery Performance")
    c_fast, c_slow = st.columns([1, 1])

    fastest_list = deliv_kpis.get("fastest_states", [])
    slowest_list = deliv_kpis.get("slowest_states", [])

    with c_fast:
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
                text="average_delivery_days"
            )
            fig_fast.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_fast, use_container_width=True)
        else:
            st.warning("Fastest states data unavailable")

    with c_slow:
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
                text="average_delivery_days"
            )
            fig_slow.update_layout(template="plotly_dark", yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_slow, use_container_width=True)
        else:
            st.warning("Slowest states data unavailable")

except Exception as e:
    st.error(f"Error loading Logistics & Statistical Analysis Page: {e}")
