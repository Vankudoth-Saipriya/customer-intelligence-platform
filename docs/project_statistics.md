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
- `customer_feature_store.py` — 23 aggregated features per unique customer (`customer_unique_id`, 96,096 total unique customers; 26,773 temporal observation customers).

### 4. Machine Learning Models (`app/ml/`)
- `segmentation.py` — Customer Segmentation via Unsupervised KMeans ($K=4$, Silhouette Score: `0.42`).
- `clv_prediction.py` — Temporal 90-Day Future Customer Value Regression via Ridge Regression ($\text{MAE} = \$3.05, \text{MedAE} = \$1.69$, evaluated against Naive $0 Baseline $\text{MAE} = \$1.25$, observation cutoff `2017-10-01`).
- `repeat_purchase_prediction.py` — Temporal Repeat Purchase Propensity Classification via Logistic Regression ($\text{PR-AUC} = 0.0169, \text{ROC-AUC} = 0.5667$).

### 5. FastAPI Inference Endpoints (`app/api/v1/`)
- `GET /health` — Health check endpoint.
- `POST /api/v1/ml/segment` — Real-time customer segment inference.
- `POST /api/v1/ml/clv` — Real-time CLV prediction.
- `POST /api/v1/ml/repeat-purchase` — Real-time repeat purchase propensity prediction.

### 6. Streamlit Dashboard App (`dashboard/`)
- `Home.py` — Executive Overview KPI dashboard landing page.
- `1_Executive_Overview.py` — Financial KPIs, Net Revenue (R$ 13.59M) vs Gross Order Value (R$ 15.84M) reconciliation, order status lifecycle audit, and revenue trends.
- `2_Customer_&_Sales_Analytics.py` — Monthly Acquisition Cohort Retention matrix (0.50% avg Month-1 retention, 3.12% overall lifetime repeat rate), Seller/Customer Pareto concentration (84.5% top-20% share), and Log-RFM customer segmentation.
- `3_Logistics_&_Statistical_Analysis.py` — Delivery SLA performance, non-parametric Mann-Whitney U test (1.66-star rating drop association, $p<0.0001$, $r=0.3421$), and Kruskal-Wallis regional state SLA test.
- `4_Predictive_Analytics.py` — Temporal observation cutoff methodology (`2017-10-01`), 90-day future spend target, baseline comparison ($1.25 Zero-Spend Baseline MAE), feature weights, and real-time score lookup.
