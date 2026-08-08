"""
AI Business Analyst Streamlit Dashboard Page.
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st

from app.dashboard.data_provider import (
    call_ai_ask_api,
    call_ai_category_report_api,
    call_ai_customer_report_api,
    call_ai_executive_summary_api,
    get_customer_segments,
    get_product_eda,
)

st.set_page_config(page_title="AI Business Analyst", page_icon="🤖", layout="wide")

st.title("🤖 AI Business Analyst")
st.markdown("Autonomous AI Business Assistant answering natural language questions and generating automated business intelligence reports.")

tab_chat, tab_exec, tab_cust, tab_cat = st.tabs([
    "💬 Interactive AI Chat",
    "📄 Executive Summary Report",
    "👤 AI Customer Intelligence Report",
    "📦 AI Product Category Report",
])

# --- TAB 1: INTERACTIVE CHAT ---
with tab_chat:
    st.subheader("💬 Ask the AI Business Analyst")
    st.markdown("Ask any business question regarding revenue, customer demographics, carrier SLA, payment methods, or ML models.")

    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {
                "role": "assistant",
                "content": "Hello! I am your AI Business Analyst. How can I help analyze your sales trajectory, customer retention, or predictive models today?",
            }
        ]

    # Sample Quick Prompts
    st.write("**Suggested Questions:**")
    qp1, qp2, qp3, qp4 = st.columns(4)
    with qp1:
        if st.button("📈 What is total revenue & AOV?"):
            st.session_state.user_question_input = "What is total revenue and average order value?"
    with qp2:
        if st.button("👥 Summary of customer clusters"):
            st.session_state.user_question_input = "Provide a summary of customer clusters and demographics."
    with qp3:
        if st.button("🚚 Delivery SLA & delay metrics"):
            st.session_state.user_question_input = "What is our carrier delivery SLA rate and average delay?"
    with qp4:
        if st.button("🤖 ML Model Accuracy & CLV"):
            st.session_state.user_question_input = "What are the ML model metrics for CLV and repeat purchase?"

    # Render previous messages
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input Box
    default_prompt = st.session_state.get("user_question_input", "")
    user_input = st.chat_input("Type your business question here...") or (default_prompt if default_prompt else None)

    if user_input:
        if "user_question_input" in st.session_state:
            del st.session_state["user_question_input"]

        # Append user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call AI API
        with st.chat_message("assistant"):
            with st.spinner("AI Analyst analyzing platform data..."):
                answer = call_ai_ask_api(user_input)
                st.markdown(answer)

        st.session_state.chat_history.append({"role": "assistant", "content": answer})


# --- TAB 2: EXECUTIVE SUMMARY ---
with tab_exec:
    st.subheader("📄 Executive Summary Business Report")
    st.markdown("Automated high-level summary compiling financial performance, customer demographics, carrier SLA, and ML insights.")

    if st.button("Generate Fresh Executive Summary"):
        with st.spinner("Generating AI Executive Business Summary..."):
            summary_md = call_ai_executive_summary_api()
            st.markdown(summary_md)
    else:
        # Load sample summary by default
        sample_path = project_root / "artifacts" / "ai" / "sample_executive_summary.md"
        if sample_path.exists():
            with open(sample_path, "r", encoding="utf-8") as f:
                st.markdown(f.read())
        else:
            st.info("Click the button above to generate an Executive Summary Report.")


# --- TAB 3: CUSTOMER REPORT ---
with tab_cust:
    st.subheader("👤 AI Customer Intelligence Report Generator")
    st.markdown("Generate a comprehensive AI dossier for a specific customer ID combining RFM metrics, segment cluster, CLV, and repeat purchase propensity.")

    try:
        df_seg = get_customer_segments()
        sample_cid = df_seg["customer_id"].iloc[0]
    except Exception:
        sample_cid = "00012a2504309823e6e38064373a51d2"

    input_cid = st.text_input("Enter Customer ID for AI Analysis:", value=sample_cid)

    if st.button("Generate AI Customer Report"):
        with st.spinner(f"AI Analyst assembling report for customer '{input_cid}'..."):
            cust_report_md = call_ai_customer_report_api(input_cid)
            st.markdown(cust_report_md)


# --- TAB 4: CATEGORY REPORT ---
with tab_cat:
    st.subheader("📦 AI Product Category Intelligence Report Generator")
    st.markdown("Generate an AI performance report for any product category.")

    try:
        prod_eda = get_product_eda()
        top_cats = list(prod_eda["product_category_analysis"]["revenue_by_category"].keys())
    except Exception:
        top_cats = ["bed_bath_table", "health_beauty", "sports_leisure", "computers_accessories"]

    selected_cat = st.selectbox("Select Product Category:", options=top_cats)

    if st.button("Generate AI Category Report"):
        with st.spinner(f"AI Analyst synthesizing metrics for '{selected_cat}'..."):
            cat_report_md = call_ai_category_report_api(selected_cat)
            st.markdown(cat_report_md)
