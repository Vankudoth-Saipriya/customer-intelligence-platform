"""
Project Statistics Calculator.

Scans the customer-intelligence-platform codebase and writes docs/project_statistics.md.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"


def generate_statistics():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    py_files = list(PROJECT_ROOT.glob("**/*.py"))
    # Exclude virtual environments if any
    py_files = [f for f in py_files if ".venv" not in str(f) and "site-packages" not in str(f)]

    total_files = len(py_files)
    total_loc = 0

    for f in py_files:
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
            total_loc += len(lines)
        except Exception:
            pass

    # Count components
    api_endpoints = 9  # /health, /ml/segment, /ml/clv, /ml/repeat-purchase, /ml/models, /ml/health, /ai/ask, /ai/customer-report, /ai/category-report, /ai/executive-summary
    ml_models = 3      # Customer Segmentation (KMeans), CLV (Random Forest), Repeat Purchase (Logistic Regression)
    dash_pages = 10    # Home.py + 9 pages under dashboard/pages/
    etl_modules = 5    # raw_loader, stg_transformer, fact_builder, loader, pipeline
    eda_modules = 5    # product, sales, payment, delivery, review
    ai_tools = 9       # Revenue, Customer, Product, Delivery, Payment, Review, Segmentation, CLV, RepeatPurchase

    stats_content = f"""# Project Statistics & Production Metrics

## 📊 Summary Overview

| Metric | Count |
| :--- | :---: |
| **Total Python Files** | `{total_files}` |
| **Total Lines of Code (LOC)** | `{total_loc:,}` |
| **FastAPI REST Endpoints** | `{api_endpoints}` |
| **Trained ML Models** | `{ml_models}` |
| **Streamlit Dashboard Pages** | `{dash_pages}` |
| **ETL Pipeline Modules** | `{etl_modules}` |
| **EDA Analytics Modules** | `{eda_modules}` |
| **AI Analyst Tools** | `{ai_tools}` |

---

## 📁 Module Inventory

### 1. ETL Pipeline Modules (`app/etl/`)
- `raw_loader.py` — CSV data ingestion engine into SQLite/PostgreSQL `raw_*` schemas.
- `stg_transformer.py` — Staging schema clean transformations (`stg_*`).
- `fact_builder.py` — Dimensional modeling into star schema fact and dimension tables (`fact_*`, `dim_*`).
- `loader.py` — Analytics data loader querying database engine.
- `pipeline.py` — End-to-end ELT pipeline orchestrator.

### 2. Exploratory Data Analysis (EDA) Modules (`app/eda/`)
- `product_analysis.py` — Category demand, product dimensions, revenue concentration & freight logistics.
- `sales_analysis.py` — Monthly/quarterly revenue trends, seasonality, order frequency, revenue concentration.
- `payment_analysis.py` — Payment method shares, installment distribution, average transaction value.
- `delivery_analysis.py` — Delivery duration, carrier delays, SLA achievement rate, regional state comparison.
- `review_analysis.py` — Star rating distribution, monthly sentiment trend, delivery delay vs. rating correlation.

### 3. Customer Feature Store (`app/features/`)
- `customer_feature_store.py` — 36 aggregated features per unique customer (`customer_unique_id`, 96,096 rows).

### 4. Machine Learning Models (`app/ml/`)
- `segmentation.py` — Customer Segmentation via Unsupervised KMeans ($k=2$, Silhouette Score: `0.5369`).
- `clv_prediction.py` — Customer Lifetime Value Regression via Random Forest ($R^2 = 0.9999$).
- `repeat_purchase_prediction.py` — Repeat Purchase Propensity Classification via Logistic Regression (ROC-AUC = 1.0000).

### 5. AI Business Analyst (`app/ai/`)
- `analyst.py` — Core `BusinessAnalyst` answering queries and generating automated reports.
- `prompt_builder.py` — Modular LLM prompt builder injecting metrics into context.
- `report_generator.py` — Sample report exporter (`sample_executive_summary.md`, `sample_business_report.md`).
- `tools.py` — 9 modular JSON data extraction tools (`RevenueTool`, `CustomerTool`, `ProductTool`, `DeliveryTool`, `PaymentTool`, `ReviewTool`, `SegmentationTool`, `CLVTool`, `RepeatPurchaseTool`).

### 6. FastAPI Inference Endpoints (`app/api/v1/`)
- `GET /health` — Health check endpoint.
- `POST /api/v1/ml/segment` — Real-time customer segment inference.
- `POST /api/v1/ml/clv` — Real-time CLV prediction.
- `POST /api/v1/ml/repeat-purchase` — Real-time repeat purchase propensity prediction.
- `GET /api/v1/ml/models` — Trained model metadata & metrics catalog.
- `GET /api/v1/ml/health` — ML Service health check.
- `POST /api/v1/ai/ask` — Natural language AI Q&A endpoint.
- `POST /api/v1/ai/customer-report` — On-demand AI customer profile report.
- `POST /api/v1/ai/category-report` — On-demand AI product category report.
- `GET /api/v1/ai/executive-summary` — Executive summary report endpoint.

### 7. Streamlit Dashboard App (`dashboard/`)
- `Home.py` — Executive Overview KPI dashboard.
- `1_Customer_Analytics.py` — Customer demographics & value tiers.
- `2_Product_Analytics.py` — Product category performance & freight.
- `3_Sales_Analytics.py` — Revenue trajectory & seasonality.
- `4_Delivery_Analytics.py` — Logistics SLA & regional state speed.
- `5_Payment_Analytics.py` — Payment method shares & installments.
- `6_Review_Analytics.py` — Customer satisfaction & sentiment.
- `7_Customer_Segmentation.py` — Cluster breakdown & real-time lookup.
- `8_CLV_Prediction.py` — Predicted CLV scatter plot & API lookup.
- `9_Repeat_Purchase.py` — Propensity histogram, gauge & API lookup.
- `10_AI_Business_Analyst.py` — Interactive AI Chat & automated report generator.
"""

    out_file = DOCS_DIR / "project_statistics.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(stats_content)

    print(f"Project statistics generated successfully -> {out_file}")


if __name__ == "__main__":
    generate_statistics()
