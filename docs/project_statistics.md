# Project Statistics & Production Metrics

## 📊 Summary Overview

| Metric | Count |
| :--- | :---: |
| **Total Python Files** | `125` |
| **Total Lines of Code (LOC)** | `13,527` |
| **FastAPI REST Endpoints** | `9` |
| **Trained ML Models** | `3` |
| **Streamlit Dashboard Pages** | `4` |
| **ETL Pipeline Modules** | `5` |
| **EDA Analytics Modules** | `5` |
| **AI Analyst Tools** | `9` |

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
- `segmentation.py` — Customer Segmentation via Unsupervised KMeans ($K=4$, Calinski-Harabasz: `66,767.45`, DB Index: `0.7974`).
- `clv_prediction.py` — Temporal Customer Lifetime Value Regression via Ridge Regression ($\text{MAE} = \$7.27, \text{MedAE} = \$3.44$, observation cutoff `2017-10-01`).
- `repeat_purchase_prediction.py` — Temporal Repeat Purchase Propensity Classification via Logistic Regression ($\text{PR-AUC} = 0.0354, \text{ROC-AUC} = 0.5632, \text{Recall} = 75.50\%$).

### 5. Internal Services (`app/services/` & `app/ai/`)
- Internal support modules (`AIService`, `MLService`, `tools.py`, `prompt_builder.py`) retained for internal background utilities and unit testing.

### 6. FastAPI Inference Endpoints (`app/api/v1/`)
- `GET /health` — Health check endpoint.
- `POST /api/v1/ml/segment` — Real-time customer segment inference.
- `POST /api/v1/ml/clv` — Real-time CLV prediction.
- `POST /api/v1/ml/repeat-purchase` — Real-time repeat purchase propensity prediction.

### 7. Streamlit Dashboard App (`dashboard/`)
- `Home.py` — Executive Overview KPI dashboard landing page.
- `1_Executive_Overview.py` — Financial KPIs, Net Revenue ($13.59M) vs Gross GMV ($16.01M) reconciliation, order status lifecycle audit, and revenue trends.
- `2_Customer_&_Sales_Analytics.py` — 12-Month Acquisition Cohort Retention matrix (<3.12% Month-1 retention), Seller/Customer Pareto concentration (82.69% top-20% share), and Log-RFM customer segmentation.
- `3_Logistics_&_Statistical_Analysis.py` — Delivery SLA performance, non-parametric Mann-Whitney U test (1.72-star rating penalty, $p<0.0001$), and Kruskal-Wallis regional state SLA test.
- `4_Predictive_Analytics.py` — Temporal observation cutoff methodology (`2017-10-01`), Ridge CLV Regression ($\text{MAE} = \$7.27, \text{MedAE} = \$3.44$), feature weights, and real-time score lookup.
