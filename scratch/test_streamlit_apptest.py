"""
Test script verifying all Streamlit pages using Streamlit AppTest framework.
"""

from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_all_streamlit_pages():
    project_root = Path(__file__).resolve().parent.parent
    dashboard_dir = project_root / "dashboard"

    pages = [
        dashboard_dir / "Home.py",
        dashboard_dir / "pages" / "1_Customer_Analytics.py",
        dashboard_dir / "pages" / "2_Product_Analytics.py",
        dashboard_dir / "pages" / "3_Sales_Analytics.py",
        dashboard_dir / "pages" / "4_Delivery_Analytics.py",
        dashboard_dir / "pages" / "5_Payment_Analytics.py",
        dashboard_dir / "pages" / "6_Review_Analytics.py",
        dashboard_dir / "pages" / "7_Customer_Segmentation.py",
        dashboard_dir / "pages" / "8_CLV_Prediction.py",
        dashboard_dir / "pages" / "9_Repeat_Purchase.py",
        dashboard_dir / "pages" / "10_AI_Business_Analyst.py",
    ]

    for p in pages:
        print(f"Testing Streamlit AppTest page: {p.name}...")
        at = AppTest.from_file(str(p), default_timeout=10.0).run()
        assert not at.exception, f"Exception occurred in {p.name}: {at.exception}"
        print(f"  [OK] {p.name} rendered successfully with 0 exceptions!")

    print("All 10 Streamlit dashboard pages tested and verified cleanly!")


if __name__ == "__main__":
    test_all_streamlit_pages()
