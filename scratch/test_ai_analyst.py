"""
Comprehensive Unit Test for AI Business Analyst module.
"""

from pathlib import Path
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from app.ai.analyst import BusinessAnalyst
from app.ai.prompt_builder import PromptBuilder
from app.ai.tools import (
    CLVTool,
    CustomerTool,
    DeliveryTool,
    PaymentTool,
    ProductTool,
    RepeatPurchaseTool,
    RevenueTool,
    ReviewTool,
    SegmentationTool,
)
from app.main import app
from app.services.ai_service import AIService


def test_ai_tools():
    print("Testing Modular Tools...")
    rev = RevenueTool().run()
    assert "total_revenue" in rev, f"RevenueTool output error: {rev}"

    cust = CustomerTool().run()
    assert "total_customers" in cust, f"CustomerTool output error: {cust}"

    prod = ProductTool().run()
    assert "total_products_analyzed" in prod, f"ProductTool output error: {prod}"

    deliv = DeliveryTool().run()
    assert "average_delivery_days" in deliv, f"DeliveryTool output error: {deliv}"

    pay = PaymentTool().run()
    assert "total_payment_value" in pay, f"PaymentTool output error: {pay}"

    rev_info = ReviewTool().run()
    assert "average_review_score" in rev_info, f"ReviewTool output error: {rev_info}"

    seg = SegmentationTool().run()
    assert "best_k" in seg, f"SegmentationTool output error: {seg}"

    clv = CLVTool().run()
    assert "selected_model" in clv, f"CLVTool output error: {clv}"

    rp = RepeatPurchaseTool().run()
    assert "selected_model" in rp, f"RepeatPurchaseTool output error: {rp}"

    print("  [OK] All 9 modular tools verified!")


def test_analyst_functions():
    print("Testing BusinessAnalyst functions...")
    analyst = BusinessAnalyst()

    ans = analyst.answer_question("What is our total revenue?")
    assert len(ans) > 20, "answer_question output too short"

    exec_summary = analyst.generate_executive_summary()
    assert "# Executive Business Summary Report" in exec_summary, "generate_executive_summary header missing"

    weekly = analyst.generate_weekly_business_report()
    assert "# Weekly Business Performance" in weekly, "generate_weekly_business_report header missing"

    cust_report = analyst.generate_customer_report("00012a2504309823e6e38064373a51d2")
    assert "AI Customer Profile" in cust_report, "generate_customer_report header missing"

    cat_report = analyst.generate_category_report("bed_bath_table")
    assert "AI Product Category Intelligence Report" in cat_report, "generate_category_report header missing"

    print("  [OK] All 5 BusinessAnalyst functions verified!")


def test_fastapi_ai_endpoints():
    print("Testing FastAPI AI REST endpoints...")
    client = TestClient(app)

    res1 = client.post("/api/v1/ai/ask", json={"question": "What is our total revenue?"})
    assert res1.status_code == 200, f"POST /ask failed: {res1.text}"
    assert "answer" in res1.json()

    res2 = client.post("/api/v1/ai/customer-report", json={"customer_id": "00012a2504309823e6e38064373a51d2"})
    assert res2.status_code == 200, f"POST /customer-report failed: {res2.text}"
    assert "report" in res2.json()

    res3 = client.post("/api/v1/ai/category-report", json={"category": "bed_bath_table"})
    assert res3.status_code == 200, f"POST /category-report failed: {res3.text}"
    assert "report" in res3.json()

    res4 = client.get("/api/v1/ai/executive-summary")
    assert res4.status_code == 200, f"GET /executive-summary failed: {res4.text}"
    assert "summary" in res4.json()

    print("  [OK] All 4 FastAPI AI endpoints verified!")


def test_streamlit_ai_page():
    print("Testing Streamlit 10_AI_Business_Analyst.py page...")
    project_root = Path(__file__).resolve().parent.parent
    page_path = project_root / "dashboard" / "pages" / "10_AI_Business_Analyst.py"

    at = AppTest.from_file(str(page_path), default_timeout=10.0).run()
    assert not at.exception, f"Streamlit page exception: {at.exception}"
    print("  [OK] Streamlit 10_AI_Business_Analyst.py page rendered cleanly!")


if __name__ == "__main__":
    test_ai_tools()
    test_analyst_functions()
    test_fastapi_ai_endpoints()
    test_streamlit_ai_page()
    print("All AI Business Analyst unit tests passed cleanly!")
