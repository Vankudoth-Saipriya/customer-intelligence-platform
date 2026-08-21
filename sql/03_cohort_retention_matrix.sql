-- ==============================================================================
-- Query 03: Monthly Customer Cohort Retention Analysis
-- Business Question: What percentage of acquired customers return to place orders in subsequent months?
-- Key Techniques: MIN() OVER() Window Function, Date Difference Math, Grouping Matrix
-- ==============================================================================

WITH CustomerAcquisition AS (
    SELECT 
        c.customer_unique_id,
        o.order_id,
        o.order_purchase_timestamp,
        MIN(o.order_purchase_timestamp) OVER (PARTITION BY c.customer_unique_id) AS first_purchase_timestamp
    FROM fact_orders o
    INNER JOIN dim_customers c 
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
),
CohortActivity AS (
    SELECT 
        customer_unique_id,
        STRFTIME('%Y-%m', first_purchase_timestamp) AS cohort_month,
        STRFTIME('%Y-%m', order_purchase_timestamp) AS activity_month,
        (
            (CAST(STRFTIME('%Y', order_purchase_timestamp) AS INTEGER) - CAST(STRFTIME('%Y', first_purchase_timestamp) AS INTEGER)) * 12 +
            (CAST(STRFTIME('%m', order_purchase_timestamp) AS INTEGER) - CAST(STRFTIME('%m', first_purchase_timestamp) AS INTEGER))
        ) AS month_number
    FROM CustomerAcquisition
),
CohortSizes AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT customer_unique_id) AS initial_cohort_size
    FROM CohortActivity
    WHERE month_number = 0
    GROUP BY cohort_month
),
RetentionMatrix AS (
    SELECT 
        ca.cohort_month,
        ca.month_number,
        COUNT(DISTINCT ca.customer_unique_id) AS active_customers
    FROM CohortActivity ca
    GROUP BY ca.cohort_month, ca.month_number
)
SELECT 
    rm.cohort_month,
    cs.initial_cohort_size,
    rm.month_number,
    rm.active_customers,
    ROUND((CAST(rm.active_customers AS REAL) / cs.initial_cohort_size) * 100.0, 2) AS retention_pct
FROM RetentionMatrix rm
INNER JOIN CohortSizes cs 
    ON rm.cohort_month = cs.cohort_month
ORDER BY rm.cohort_month ASC, rm.month_number ASC;
