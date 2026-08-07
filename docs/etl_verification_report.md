# ETL Pipeline End-to-End Verification Report

## Executive Summary

- **Overall Pipeline Status**: `WARNING`
- **Total Pipeline Execution Time**: `26.33 seconds`
- **Total Execution Time (End-to-End Verification)**: `26.46 seconds`
- **Checkpoint Cleared on Success**: `True`
- **Database Engine Used**: `SQLite / PostgreSQL Compatible`

---

## Processing Sequence & Extraction Summary

| Processing Order | Dataset Name | Source CSV File | Rows Extracted | Columns Count | Extraction Time (s) |
| :--- | :--- | :--- | :---: | :---: | :---: |
| 1 | `translations` | `product_category_name_translation.csv` | 71 | 2 | 0.0000 |
| 2 | `customers` | `olist_customers_dataset.csv` | 99,441 | 5 | 0.0000 |
| 3 | `products` | `olist_products_dataset.csv` | 32,951 | 9 | 0.0000 |
| 4 | `orders` | `olist_orders_dataset.csv` | 99,441 | 8 | 0.0000 |
| 5 | `order_items` | `olist_order_items_dataset.csv` | 112,650 | 7 | 0.0000 |
| 6 | `payments` | `olist_order_payments_dataset.csv` | 103,886 | 5 | 0.0000 |
| 7 | `reviews` | `olist_order_reviews_dataset.csv` | 99,224 | 7 | 0.0000 |

---

## Validation Summary

- **Total Datasets Evaluated**: `7`
- **Passed Datasets**: `7`
- **Failed Datasets**: `0`
- **Validation Overall Status**: `WARNING`

### Detailed Dataset Validation Breakdown

| Dataset Name | Total Rows | Status | Passed Checks | Failed Checks | Warnings | Critical Count | Error Count | Warning Count |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `translations` | 71 | `PASSED` | 9 | 0 | 0 | 0 | 0 | 0 |
| `customers` | 99,441 | `PASSED` | 11 | 0 | 0 | 0 | 0 | 0 |
| `products` | 32,951 | `WARNING` | 10 | 0 | 1 | 0 | 0 | 1 |
| `orders` | 99,441 | `WARNING` | 11 | 0 | 1 | 0 | 0 | 1 |
| `order_items` | 112,650 | `PASSED` | 9 | 0 | 0 | 0 | 0 | 0 |
| `payments` | 103,886 | `PASSED` | 11 | 0 | 0 | 0 | 0 | 0 |
| `reviews` | 99,224 | `PASSED` | 10 | 0 | 0 | 0 | 0 | 0 |

---

## Transformation Summary

- **Total Datasets Transformed**: `7`
- **Total Transformation Time**: `2.3388 seconds`

### Detailed Dataset Transformation Breakdown

| Dataset Name | Initial Rows | Final Rows | Rows Dropped | Rows Modified | Transformation Steps Applied | Time (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `translations` | 71 | 71 | 0 | 0 | 2 | 0.0041 |
| `customers` | 99,441 | 99,441 | 0 | 397,764 | 6 | 0.3629 |
| `products` | 32,951 | 32,951 | 0 | 98,228 | 5 | 0.0555 |
| `order_items` | 112,650 | 112,650 | 0 | 225,300 | 4 | 0.3873 |
| `orders` | 99,441 | 99,441 | 0 | 588,158 | 8 | 0.8652 |
| `payments` | 103,886 | 103,886 | 0 | 207,772 | 4 | 0.1593 |
| `reviews` | 99,224 | 99,224 | 0 | 309,121 | 5 | 0.5025 |

---

## Database Loading & Ingestion Summary

- **Total Datasets Attempted**: `7`
- **Total Rows Attempted**: `547,664`
- **Total Rows Inserted**: `547,593`
- **Total Rows Skipped**: `71`
- **Loading Execution Time**: `21.4554 seconds`
- **All Tables Verified**: `True`

### Detailed Database Loading Breakdown

| Dataset Name | Rows Attempted | Rows Inserted | Rows Skipped | Success Rate | Verified | Verification Time (s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `customers` | 99,441 | 99,441 | 0 | 100.00% | `True` | 0.0036 |
| `products` | 32,951 | 32,951 | 0 | 100.00% | `True` | 0.0012 |
| `orders` | 99,441 | 99,441 | 0 | 100.00% | `True` | 0.0058 |
| `order_items` | 112,650 | 112,650 | 0 | 100.00% | `True` | 0.0071 |
| `payments` | 103,886 | 103,886 | 0 | 100.00% | `True` | 0.0067 |
| `reviews` | 99,224 | 99,224 | 0 | 100.00% | `True` | 0.0067 |
| `translations` | 71 | 0 | 71 | 0.00% | `True` | 0.0000 |

---

## SQL Post-Load Verification Query Results

### 1. Database Table Row Counts

| Table Name | Inserted DB Row Count | Match Extracted/Transformed |
| :--- | :---: | :---: |
| `customers` | 99,441 | ✅ MATCH |
| `products` | 32,951 | ✅ MATCH |
| `orders` | 99,441 | ✅ MATCH |
| `order_items` | 112,650 | ✅ MATCH |
| `payments` | 103,886 | ✅ MATCH |
| `reviews` | 99,224 | ✅ MATCH |

### 2. Foreign Key Integrity Audit

| Foreign Key Check Description | Violation Count | Status |
| :--- | :---: | :---: |
| `orders_without_customer` | 0 | ✅ PASSED |
| `items_without_order` | 0 | ✅ PASSED |
| `items_without_product` | 0 | ✅ PASSED |
| `payments_without_order` | 0 | ✅ PASSED |
| `reviews_without_order` | 0 | ✅ PASSED |

### 3. Null Constraint Audit

| Non-Nullable Column Group | Violation Count | Status |
| :--- | :---: | :---: |
| `null_customer_ids` | 0 | ✅ PASSED |
| `null_product_ids` | 0 | ✅ PASSED |
| `null_order_ids` | 0 | ✅ PASSED |
| `null_item_ids` | 0 | ✅ PASSED |
| `null_payment_ids` | 0 | ✅ PASSED |
| `null_review_ids` | 0 | ✅ PASSED |

### 4. Primary Key Uniqueness Audit

| Primary / Composite Key Group | Duplicate Key Count | Status |
| :--- | :---: | :---: |
| `customers_duplicate_pks` | 0 | ✅ PASSED |
| `products_duplicate_pks` | 0 | ✅ PASSED |
| `orders_duplicate_pks` | 0 | ✅ PASSED |
| `order_items_duplicate_pks` | 0 | ✅ PASSED |
| `payments_duplicate_pks` | 0 | ✅ PASSED |
| `reviews_duplicate_pks` | 0 | ✅ PASSED |

---

## Verification Conclusion

All ETL pipeline stages (**Extract**, **Validate**, **Transform**, **Load**, and **Post-Load Verification**) completed cleanly with zero CRITICAL failures.

1. **Extraction**: All 7 raw CSV files were successfully read into memory.
2. **Validation**: All schema & domain checks passed without halting execution.
3. **Transformation**: All operational derivations (delivery delays, fulfillment metrics, category translations, volumetric weights) were correctly computed.
4. **Database Ingestion**: All 6 target domain tables were populated in foreign-key safe order (`customers` -> `products` -> `orders` -> `order_items` -> `payments` -> `reviews`).
5. **SQL Integrity Verification**: SQL integrity audits confirmed **0 foreign key violations**, **0 null violations**, and **0 duplicate primary keys**.
