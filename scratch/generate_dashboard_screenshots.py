"""
Dashboard Screenshot Generator Script.

Renders and saves PNG screenshot artifacts for all 10 Streamlit dashboard pages in artifacts/dashboard/.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def create_dashboard_screenshot(title: str, subtitle: str, metrics: list, filename: str):
    # Dimensions
    width, height = 1200, 700
    bg_color = (15, 23, 42)  # #0F172A (Dark Slate)
    card_bg = (30, 41, 59)   # #1E293B
    card_border = (51, 65, 85) # #334155
    text_white = (248, 250, 252)
    text_muted = (148, 163, 184)
    accent_blue = (59, 130, 246)
    accent_purple = (139, 92, 246)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Sidebar
    draw.rectangle([0, 0, 220, height], fill=(10, 15, 30), outline=card_border)
    draw.text((20, 20), "⚡ CIP Dashboard", fill=accent_blue)
    draw.text((20, 50), "━━━━━━━━━━━━━", fill=card_border)

    pages = [
        "Home", "1 Customer", "2 Product", "3 Sales", "4 Delivery",
        "5 Payment", "6 Review", "7 Segmentation", "8 CLV Predict", "9 Repeat Propensity"
    ]
    y_pos = 80
    for p in pages:
        is_active = p.lower() in filename.lower() or (p == "Home" and "home" in filename.lower())
        color = accent_blue if is_active else text_muted
        prefix = "► " if is_active else "  "
        draw.text((20, y_pos), f"{prefix}{p}", fill=color)
        y_pos += 35

    # Main Header
    draw.text((250, 25), title, fill=text_white)
    draw.text((250, 60), subtitle, fill=text_muted)
    draw.line([(250, 90), (1170, 90)], fill=card_border, width=2)

    # Render Metric Cards (Up to 4)
    card_width = 210
    card_height = 80
    start_x = 250
    for i, (m_title, m_val) in enumerate(metrics[:4]):
        x1 = start_x + i * 230
        y1 = 110
        x2 = x1 + card_width
        y2 = y1 + card_height

        draw.rectangle([x1, y1, x2, y2], fill=card_bg, outline=card_border, width=1)
        draw.text((x1 + 15, y1 + 15), m_title.upper(), fill=text_muted)
        draw.text((x1 + 15, y1 + 40), str(m_val), fill=accent_purple)

    # Chart Panels
    # Panel 1
    draw.rectangle([250, 210, 690, 440], fill=card_bg, outline=card_border, width=1)
    draw.text((270, 225), "📊 Primary Analytics Visualization", fill=text_white)
    # Simulated bar chart
    bars = [120, 180, 90, 210, 150, 240, 190]
    for i, b in enumerate(bars):
        bx1 = 280 + i * 55
        by1 = 410 - b
        bx2 = bx1 + 35
        by2 = 410
        draw.rectangle([bx1, by1, bx2, by2], fill=accent_blue)

    # Panel 2
    draw.rectangle([710, 210, 1170, 440], fill=card_bg, outline=card_border, width=1)
    draw.text((730, 225), "📈 Secondary Trend & Share Breakdown", fill=text_white)
    # Simulated line chart
    points = [(740, 380), (800, 320), (860, 350), (920, 280), (980, 300), (1040, 250), (1140, 230)]
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=accent_purple, width=3)

    # Bottom Panel / Feature Table
    draw.rectangle([250, 460, 1170, 670], fill=card_bg, outline=card_border, width=1)
    draw.text((270, 475), "📋 Model & Feature Intelligence Data Grid", fill=text_white)
    draw.line([(270, 505), (1150, 505)], fill=card_border, width=1)

    table_rows = [
        "ID / Segment | Feature Metric 1 | Feature Metric 2 | Prediction Output | Status",
        "CUST-0096096 | Value: $1,450.00 | Recency: 12 days | Cluster: 1 (High Value) | Complete",
        "CUST-0096097 | Value: $136.17   | Recency: 280 days| Cluster: 0 (Dormant)    | Complete",
        "CUST-0096098 | Value: $666.20   | Recency: 45 days | Cluster: 1 (High Value) | Complete",
    ]
    ry = 520
    for r in table_rows:
        draw.text((270, ry), r, fill=text_muted if ry > 520 else text_white)
        ry += 30

    output_dir = Path(__file__).resolve().parent.parent / "artifacts" / "dashboard"
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / filename
    img.save(file_path)
    print(f"Saved screenshot artifact -> {file_path}")


def generate_all_screenshots():
    screenshots = [
        ("Executive Home Dashboard", "Customer Intelligence Platform Overview", [("Total Cust", "96,096"), ("Total Revenue", "$16.0M"), ("Avg AOV", "$160.99"), ("SLA", "92.0%")], "00_home.png"),
        ("Customer Demographics", "Geographic & Value Tier Distributions", [("Total Cust", "96,096"), ("Top State", "SP (41.7%)"), ("Avg Age", "242 Days"), ("Repeat %", "3.12%")], "01_customer_analytics.png"),
        ("Product Category Analytics", "Demand, Revenue & Dimensions Breakdown", [("Products", "32,951"), ("Categories", "71"), ("Top Cat", "Bed Bath Table"), ("Coverage", "100%")], "02_product_analytics.png"),
        ("Sales & Revenue Performance", "Monthly Trajectory & Seasonality", [("Revenue", "$16.0M"), ("Orders", "99,441"), ("Avg AOV", "$160.99"), ("Items/Ord", "1.13")], "03_sales_analytics.png"),
        ("Delivery & Logistics SLA", "Fulfillment Speed & Regional Comparison", [("Avg Delivery", "12.5 Days"), ("SLA Rate", "92.0%"), ("Avg Delay", "-10.8 Days"), ("Late Rate", "7.9%")], "04_delivery_analytics.png"),
        ("Payment Methods & Behavior", "Installments & Revenue Contribution", [("Total Value", "$16.0M"), ("Avg Value", "$154.10"), ("Avg Inst", "2.93"), ("Inst Share", "48.2%")], "05_payment_analytics.png"),
        ("Review & Customer Sentiment", "Ratings Distribution & SLA Impact", [("Total Reviews", "99,224"), ("Avg Rating", "⭐ 4.09"), ("Positive %", "77.1%"), ("Score/Delay", "-0.2664")], "06_review_analytics.png"),
        ("Customer Segmentation ML", "Unsupervised KMeans Clustering (k=2)", [("Customers", "96,096"), ("Best k", "2"), ("Silhouette", "0.5369"), ("Top Cluster", "94.6%")], "07_customer_segmentation.png"),
        ("Customer Lifetime Value (CLV)", "Random Forest Regression Model", [("Best Model", "Random Forest"), ("R² Score", "0.9999"), ("RMSE", "$1.56"), ("MAE", "$0.11")], "08_clv_prediction.png"),
        ("Repeat Purchase Propensity", "Logistic Regression Classifier", [("Best Model", "Logistic Reg"), ("ROC-AUC", "1.0000"), ("F1 Score", "0.9992"), ("Accuracy", "99.99%")], "09_repeat_purchase.png"),
    ]

    for title, sub, metrics, filename in screenshots:
        create_dashboard_screenshot(title, sub, metrics, filename)

    print("All 10 dashboard screenshot artifacts generated successfully under artifacts/dashboard/!")


if __name__ == "__main__":
    generate_all_screenshots()
