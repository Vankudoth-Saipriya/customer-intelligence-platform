# Streamlit Dashboard Screenshots & Presentation Catalog

This document indexes all high-definition visual screenshot artifacts generated for the Customer Intelligence Platform under `artifacts/dashboard/`, detailing what each dashboard page demonstrates and providing the recommended presentation order for GitHub and executive reviews.

---

## 🖼️ Primary Cover Image

### 1. Dashboard Overview Collage Cover
- **File**: `artifacts/dashboard/dashboard_overview.png`
- **Resolution**: `2560 x 1440`
- **Demonstrates**: Executive high-resolution collage combining the Home Overview, Customer Analytics, Sales Performance, Customer Segmentation, AI Business Analyst interface, and key platform capabilities summary.
- **Recommended Placement**: Hero Banner at top of `README.md`.

---

## 📊 Module Screenshots & Presentation Order

### 1. Executive Home Overview
- **File**: `artifacts/dashboard/00_home.png`
- **Demonstrates**: High-level platform KPIs (Total Customers: 96,096, Total Revenue: $16.0M, AOV: $160.99, Delivery SLA: 92.0%) and navigation cards linking to all exploratory analytics & machine learning modules.
- **Suggested Order**: 1

### 2. Customer Analytics
- **File**: `artifacts/dashboard/01_customer_analytics.png`
- **Demonstrates**: Top 20 customer state density (SP 41.7%), customer value tier distribution pie chart (High Value, Medium Value, Low Value), monthly customer acquisition growth, and RFM statistics table.
- **Suggested Order**: 2

### 3. Product Analytics
- **File**: `artifacts/dashboard/02_product_analytics.png`
- **Demonstrates**: Top 15 product categories by revenue & order volume, product weight & volume physical distributions, category translation coverage (100%), and freight correlation metrics.
- **Suggested Order**: 3

### 4. Sales & Revenue Performance
- **File**: `artifacts/dashboard/03_sales_analytics.png`
- **Demonstrates**: Historical monthly revenue trend trajectory, quarterly revenue bar breakdown, weekday order distribution, peak revenue months, and top customer revenue concentration tiers.
- **Suggested Order**: 4

### 5. Delivery & Logistics SLA
- **File**: `artifacts/dashboard/04_delivery_analytics.png`
- **Demonstrates**: Order delivery time duration histogram, early/late delay pie chart, carrier SLA achievement rate, and regional state delivery speed ranking (fastest vs. slowest states).
- **Suggested Order**: 5

### 6. Payment Analytics
- **File**: `artifacts/dashboard/06_payment_analytics.png` (or `05_payment_analytics.png`)
- **Demonstrates**: Payment method revenue contribution pie chart, average transaction value by method, installment count distribution, and installment revenue share.
- **Suggested Order**: 6

### 7. Review & Sentiment Analytics
- **File**: `artifacts/dashboard/06_review_analytics.png`
- **Demonstrates**: Review star rating distribution (1-5 stars), monthly rating sentiment trend, delivery speed bucket vs. rating score impact, and highest/lowest rated product categories.
- **Suggested Order**: 7

### 8. Customer Segmentation ML
- **File**: `artifacts/dashboard/07_customer_segmentation.png`
- **Demonstrates**: Unsupervised KMeans cluster size breakdown ($k=2$, Silhouette Score: `0.5369`), segment revenue contribution, and real-time customer ID lookup calling `POST /api/v1/ml/segment`.
- **Suggested Order**: 8

### 9. Customer Lifetime Value (CLV) Prediction
- **File**: `artifacts/dashboard/08_clv_prediction.png`
- **Demonstrates**: Supervised Random Forest Regressor ($R^2 = 0.9999$, MAE = $0.11), actual vs. predicted revenue scatter plot, top high-CLV customers table, and real-time API lookup calling `POST /api/v1/ml/clv`.
- **Suggested Order**: 9

### 10. Repeat Purchase Propensity Prediction
- **File**: `artifacts/dashboard/09_repeat_purchase.png`
- **Demonstrates**: Supervised Logistic Regression Classifier ($\text{ROC-AUC} = 1.0000$, $\text{F1} = 0.9992$), repeat propensity score histogram, probability gauge, and real-time API lookup calling `POST /api/v1/ml/repeat-purchase`.
- **Suggested Order**: 10

### 11. AI Business Analyst
- **File**: `artifacts/dashboard/10_ai_business_analyst.png`
- **Demonstrates**: Autonomous conversational AI chat interface, automated Executive Business Summary generator, customer profile dossier generator, and product category intelligence generator.
- **Suggested Order**: 11
