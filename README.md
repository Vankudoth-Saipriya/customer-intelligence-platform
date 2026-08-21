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
| **🛢️ Analytical SQL Suite** | `6` SQL Analytics Workflows (`CTEs`, `LAG`, `SUM OVER`, `MIN OVER`, `ROW_NUMBER`, `NTILE`) |
| **📊 Financial Reconciliation** | `$13.59M` Net Delivered Revenue vs `$16.01M` Gross GMV ($270.4K$ lost volume) |
| **🔬 Inferential Statistics** | Non-parametric Mann-Whitney U ($U = 1.52 \times 10^8, p < 0.0001, r = 0.5534$) & Kruskal-Wallis tests |
| **🎯 Customer Analytics** | 12-Month Cohort Retention Matrix (<3.12% Month-1 retention) & Seller Pareto (Top 20% = 82.69% revenue) |
| **🤖 Leakage-Free ML** | Temporal Cutoff (`2017-10-01`), Log-RFM KMeans ($K=4$), Ridge CLV Regression ($\text{MAE} = \$7.27$) |
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
  Exploratory & Diagnostic Business Analytics (RFM, 12-Month Cohorts, Seller Pareto 80/20)
      ↓
  Inferential Statistical Testing (Mann-Whitney U SLA Test & Kruskal-Wallis Regional Analysis)
      ↓
  Temporal Customer Feature Store & Leakage-Free ML (Ridge CLV Regression, Cutoff: 2017-10-01)
      ↓
  Unified 4-Module Interactive Executive BI Dashboard (Streamlit)
```

---

## 🛠️ Analytical Modules & Dashboard Structure

1. **📈 Executive Overview (`1_Executive_Overview.py`)**:
   - Financial KPIs ($99,441$ orders, $\$16.01\text{M}$ Gross GMV, $\$13.59\text{M}$ Net Delivered Revenue).
   - Data Quality Audit reconciling delivered vs canceled order lifecycle drops.
   - Monthly net revenue trend & cumulative run-rate trajectory.

2. **👥 Customer & Sales Analytics (`2_Customer_&_Sales_Analytics.py`)**:
   - 12-Month Acquisition Cohort Retention Heatmap (retention decays $<3.12\%$ by Month 1).
   - Seller & Customer Pareto Revenue Concentration (top 20% sellers generate 82.69% revenue).
   - Log-RFM Customer Segmentation Persona Distribution ($K=4$).

3. **🚚 Logistics & Statistical Analysis (`3_Logistics_&_Statistical_Analysis.py`)**:
   - Carrier delivery SLA achievement rate ($92.0\%$) and regional state speed rankings.
   - Mann-Whitney U test finding statistically significant association between delivery SLA breaches and lower review scores ($U = 1.52 \times 10^8, p < 0.0001, r = 0.5534$, 1.72-star penalty).
   - Kruskal-Wallis H test confirming regional delivery delay variance ($H = 268.4, p < 0.0001$).

4. **🤖 Predictive Decision Support (`4_Predictive_Analytics.py`)**:
   - Temporal observation cutoff methodology (`2017-10-01`), eliminating feature leakage.
   - Ridge CLV Regression predicting 1-year future spend ($\text{MAE} = \$7.27, \text{MedAE} = \$3.44$).
   - Trained model feature weights interpretability and real-time inference lookup.

---

## 📝 Resumé Bullets

**Customer Intelligence & E-Commerce Analytics | Self Project [XX 'XX - XX 'XX]**

- **SQL + Data Quality**: Built SQL analytics workflows using CTEs and window functions to reconcile $16.01M GMV across 99,441 orders and audit order-status data quality.
- **EDA + Customer/Sales Analytics**: Built a Streamlit dashboard for RFM, cohort retention and seller Pareto analytics, revealing <3.12% Month-1 retention and 82.69% top-20% revenue concentration.
- **Statistics + Business Insights**: Conducted non-parametric hypothesis testing, finding a statistically significant association between delivery delays and a 1.72-star lower review rating (p<0.0001).
- **RFM + Targeted ML**: Applied Log-RFM clustering to define 4 customer personas and trained a leakage-controlled Ridge model for future customer value using a temporal cutoff.

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
