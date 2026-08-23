<div align="center">

# ⚡ Customer Intelligence & E-Commerce Analytics

### *End-to-End E-Commerce Analytics, Analytical SQL Workflows, Inferential Statistics & Predictive Analytics Platform*

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688.svg?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.46.0-FF4B4B.svg?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3.0+-F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Plotly](https://img.shields.io/badge/Plotly-6.8.0-3F4F75.svg?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

</div>

---

## ⚡ Project Highlights

| Metric / Highlight | Count / Detail |
| :--- | :--- |
| **📈 Processed Data Volume** | `550,759` Operational Records across 9 Relational Tables ($99,441$ Orders, $96,096$ Customers) |
| **🛢️ Analytical SQL Suite** | `6` Production SQL Workflows (`CTEs`, `LAG`, `SUM OVER`, `MIN OVER`, `ROW_NUMBER`, `NTILE`) |
| **📊 Financial Metrics** | `R$ 13.59M` Delivered Item Revenue, `R$ 15.84M` Gross Order Value (Price+Freight), `R$ 16.01M` Payments |
| **🔬 Inferential Statistics** | Non-parametric Mann-Whitney U ($U = 1.94 \times 10^8, p < 0.0001, r = 0.3421$) & Kruskal-Wallis tests |
| **🎯 Customer Analytics** | `3.12%` Overall Lifetime Repeat Buyer Rate (2,997/96,096), `0.50%` Avg Month-1 Cohort Retention, Seller Pareto (Top 20% = 84.5% revenue) |
| **🤖 Predictive Analytics** | Leakage-Free Temporal Cutoff (`2017-10-01`), 90-Day Future Value Target, Evaluated against Naive $0 Baseline ($1.25 MAE) |
| **🖥️ Dashboard UI** | `4` Consolidated Story-Driven Streamlit Modules with Executive Business Insight Cards |
| **🧪 Automated Testing** | `16` Pytest Verification Files (100% Pass Rate) |

---

## 📌 Project Analytical Workflow

```
Raw Data Ingestion (550,759 Operational Records across 9 Datasets)
      ↓
  ELT Pipeline & PostgreSQL/SQLite Star Schema Modeling (99,441 Orders, 96,096 Customers)
      ↓
  SQL Analytics Workflows (6 Raw SQL Query Scripts in sql/) & Data Quality Audit
      ↓
  Exploratory & Diagnostic Business Analytics (RFM, Monthly Cohorts, Seller Pareto 80/20)
      ↓
  Inferential Statistical Testing (Mann-Whitney U SLA Test & Kruskal-Wallis Regional Analysis)
      ↓
  Temporal Customer Feature Store & 90-Day Predictive Value (Cutoff: 2017-10-01, Baseline Evaluation)
      ↓
  Unified 4-Module Interactive Executive BI Dashboard (Streamlit)
```

---

## 🛠️ Analytical Modules & Dashboard Structure

1. **📈 Executive Overview (`1_Executive_Overview.py`)**:
   - Financial KPIs ($99,441$ orders, $\text{R\$ } 15.84\text{M}$ Gross Order Value, $\text{R\$ } 13.59\text{M}$ Delivered Item Revenue).
   - Data Quality Audit reconciling order lifecycle status drops ($96,478$ delivered orders).
   - Monthly net revenue trend & cumulative run-rate trajectory.

2. **👥 Customer & Sales Analytics (`2_Customer_&_Sales_Analytics.py`)**:
   - Monthly Acquisition Cohort Retention Heatmap (average Month-1 retention of **$0.50\%$**, peak **$0.72\%$**).
   - Lifetime repeat customer rate (**$3.12\%$** overall repeat buyers across 96,096 unique customer entities).
   - Seller & Customer Pareto Revenue Concentration (top 20% sellers generate **84.5%** of revenue).
   - Log-RFM Customer Segmentation Persona Distribution ($K=4$).

3. **🚚 Logistics & Statistical Analysis (`3_Logistics_&_Statistical_Analysis.py`)**:
   - Carrier delivery SLA achievement rate (**$92.9\%$**) and regional state speed rankings.
   - Mann-Whitney U test finding a statistically significant association between delivery SLA breaches and lower review scores ($U = 1.94 \times 10^8, p < 0.0001, r = 0.3421$, 1.66-star penalty: 4.23 vs 2.57 stars).
   - Kruskal-Wallis H test confirming regional delivery delay variance across states ($H = 2,840.5, p < 0.0001$).

4. **🤖 Predictive Decision Support (`4_Predictive_Analytics.py`)**:
   - Temporal observation cutoff methodology (`2017-10-01`), eliminating feature leakage.
   - Fixed 90-day future spend target (`2017-10-01` to `2017-12-30`).
   - Baseline-grounded evaluation against Naive Zero-Spend Baseline MAE (**$1.25**).

---

## 📝 Resumé Bullets

**Customer Intelligence & E-Commerce Analytics | Self Project [XX 'XX – XX 'XX]**

• Built SQL analytics workflows using CTEs and window functions to audit data quality and analyze 99.4K orders representing R$15.84M gross order value across 9 relational datasets.

• Developed a 4-page Streamlit dashboard for MoM revenue, RFM, cohort and Pareto analytics, revealing 84.5% revenue concentration among the top 20% of sellers.

• Conducted a Mann-Whitney U test, identifying a statistically significant 1.66-star rating drop associated with delivery delays (p<0.0001, effect size r=0.34).

• Applied Log-RFM K-Means (K=4) to segment 96.1K customers, identifying an at-risk, high-value persona representing 32.8% of customers and 58.0% of gross order value.

---

## 🧪 Automated Testing & Verification

Run the full pytest suite:
```bash
pytest tests/ -v
```

All 16 test modules verify data loaders, feature cutoff enforcement, analytics engines, ML predictors, and API health endpoints.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
