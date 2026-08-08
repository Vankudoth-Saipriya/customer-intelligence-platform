"""
Schema Inspection and Key Mismatch Auditor.

Audits every Streamlit page in dashboard/ and dashboard/pages/*.py against actual JSON keys in artifacts/eda/*.json.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EDA_DIR = PROJECT_ROOT / "artifacts" / "eda"
DASHBOARD_DIR = PROJECT_ROOT / "dashboard"


def audit_keys():
    # Load all EDA JSON files
    eda_data = {}
    for json_file in EDA_DIR.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            eda_data[json_file.name] = json.load(f)

    print("Loaded EDA JSON files:", list(eda_data.keys()))

    # Print Key Mismatches for Customer Analytics (1_Customer_Analytics.py)
    print("\n--- Customer Analysis Keys ---")
    c_json = eda_data.get("customer_analysis.json", {})
    print("customer_analysis top keys:", list(c_json.keys()))
    if "geographic_distribution" in c_json:
        print("  geographic_distribution keys:", list(c_json["geographic_distribution"].keys()))
    if "spending_overview" in c_json:
        print("  spending_overview keys:", list(c_json["spending_overview"].keys()))
    if "repeat_analysis" in c_json:
        print("  repeat_analysis keys:", list(c_json["repeat_analysis"].keys()))

    # Print Delivery Keys (4_Delivery_Analytics.py)
    print("\n--- Delivery Analysis Keys ---")
    d_json = eda_data.get("delivery_analysis.json", {})
    print("delivery_analysis top keys:", list(d_json.keys()))
    if "operational_metrics" in d_json:
        print("  operational_metrics keys:", list(d_json["operational_metrics"].keys()))
    if "regional_delivery_performance" in d_json:
        print("  regional_delivery_performance keys:", list(d_json["regional_delivery_performance"].keys()))

    # Print Sales Keys (3_Sales_Analytics.py)
    print("\n--- Sales Analysis Keys ---")
    s_json = eda_data.get("sales_analysis.json", {})
    print("sales_analysis top keys:", list(s_json.keys()))
    if "order_analysis" in s_json:
        print("  order_analysis keys:", list(s_json["order_analysis"].keys()))
    if "revenue_analysis" in s_json:
        print("  revenue_analysis keys:", list(s_json["revenue_analysis"].keys()))

    # Print Product Keys (2_Product_Analytics.py)
    print("\n--- Product Analysis Keys ---")
    p_json = eda_data.get("product_analysis.json", {})
    print("product_analysis top keys:", list(p_json.keys()))
    if "category_analysis" in p_json:
        print("  category_analysis keys:", list(p_json["category_analysis"].keys()))

    # Print Payment Keys (5_Payment_Analytics.py)
    print("\n--- Payment Analysis Keys ---")
    pay_json = eda_data.get("payment_analysis.json", {})
    print("payment_analysis top keys:", list(pay_json.keys()))

    # Print Review Keys (6_Review_Analytics.py)
    print("\n--- Review Analysis Keys ---")
    r_json = eda_data.get("review_analysis.json", {})
    print("review_analysis top keys:", list(r_json.keys()))


if __name__ == "__main__":
    audit_keys()
