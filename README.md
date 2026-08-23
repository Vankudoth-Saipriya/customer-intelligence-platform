# Customer Intelligence & E-Commerce Analytics

## Overview
This project presents an end-to-end e-commerce analytics platform evaluating 99.4K orders and R$15.84M in gross order value from the Olist Brazilian marketplace dataset. By combining analytical SQL queries, non-parametric inferential statistics, and Log-RFM customer segmentation, the platform diagnoses customer retention trends, seller revenue concentration, and delivery service-level agreement (SLA) impacts. All analytical workflows and business findings are synthesized into an interactive 4-page Streamlit dashboard.

## Key Analytics
- **SQL Analytics & Data Quality**: Engineered multi-stage SQL workflows (`CTEs`, `LAG`, `SUM OVER`, `NTILE`) over 9 relational tables to audit order status lifecycles and aggregate transactional metrics.
- **MoM Revenue Trajectory**: Evaluated monthly net revenue trends, order volume trajectory, and average order value across 25 active calendar months.
- **RFM Analysis**: Computed Recency, Frequency, and Monetary metrics alongside quantile scoring to evaluate customer purchasing habits.
- **Cohort Retention**: Analyzed 12-month acquisition cohort matrices to track post-purchase customer retention decay.
- **Seller Pareto Distribution**: Evaluated seller revenue concentration using cumulative window functions to identify top-performing merchant tiers.
- **Logistics & Satisfaction Analysis**: Applied non-parametric inferential statistics (Mann-Whitney U and Kruskal-Wallis tests) to evaluate the association between delivery SLA breaches and review ratings.
- **Log-RFM K-Means Segmentation**: Preprocessed log-transformed and standardized RFM features using K-Means ($K=4$) to partition customers into business-interpretable personas.

## Key Findings
- **Data Volume**: Analyzed 99.4K orders and 96.1K unique customers representing R$15.84M in gross order value.
- **Seller Revenue Concentration**: The top 20% of marketplace sellers account for 84.5% of total revenue.
- **Logistics SLA Association**: Late delivery SLA breaches are associated with a statistically significant 1.66-star drop in review score ($p < 0.0001, r = 0.34$).
- **Customer Personas**: Identified 4 distinct customer personas, highlighting an at-risk high-value segment (32.8% of customers) that accounts for 58.0% of total gross order value with an average recency of 347 days.

## Dashboard
The Streamlit application provides interactive exploration across four focused modules:
1. **Executive Overview**: Financial KPIs, order status data quality audit, and monthly revenue trajectory.
2. **Customer & Sales Analytics**: Acquisition cohort retention heatmaps, seller Pareto share, and RFM distributions.
3. **Logistics & Statistical Analysis**: Delivery SLA performance, Mann-Whitney U test results, and regional delivery delay rankings.
4. **Predictive Analytics**: 90-day future value target formulation, baseline-grounded temporal evaluation, and feature importance.

## Tech Stack
- **Languages**: Python, SQL (ANSI / PostgreSQL / SQLite)
- **Core Libraries**: Pandas, NumPy, SciPy, Scikit-learn
- **Visualization & UI**: Streamlit, Plotly
- **Testing & API**: Pytest, FastAPI

## Project Structure
```
customer-intelligence-platform/
├── app/                  # Analytics engine, data loaders, and ML models
├── dashboard/            # 4-page Streamlit application
├── sql/                  # Analytical SQL query scripts
├── tests/                # Automated pytest test suite
├── data/                 # Raw dataset files
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## How to Run

1. **Install Dependencies**:
```bash
pip install -r requirements.txt
```

2. **Run Streamlit Dashboard**:
```bash
streamlit run dashboard/Home.py
```

3. **Run Tests**:
```bash
pytest tests/ -v
```

## Limitations
- **Observational Data**: Statistical associations between delivery delays and review scores do not establish direct causality.
- **Historical Scope**: The dataset covers a fixed historical period (2016–2018) for Brazilian e-commerce operations.
- **Descriptive Segmentation**: K-Means clustering defines descriptive customer personas rather than an active real-time churn prediction model.
- **Zero-Inflation**: Low repeat purchase rate (3.12%) introduces high zero-spending prevalence in short-term future value windows.

## Dataset
This project uses the publicly available [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) on Kaggle, comprising 550,759 operational records across 9 relational datasets.
