-- ==============================================================================
-- Query 01: Customer RFM Segmentation & Behavioral Profiling
-- Business Question: How are customers distributed across Recency, Frequency, and Monetary value?
-- Key Techniques: Multi-table JOINs, CTEs, Aggregations, CASE WHEN scoring, Date Arithmetic
-- ==============================================================================

WITH CustomerOrders AS (
    SELECT 
        c.customer_unique_id,
        c.customer_state,
        COUNT(DISTINCT o.order_id) AS total_orders,
        MAX(o.order_purchase_timestamp) AS last_purchase_date,
        SUM(p.payment_value) AS total_monetary_spend,
        AVG(p.payment_value) AS avg_order_value
    FROM dim_customers c
    INNER JOIN fact_orders o 
        ON c.customer_id = o.customer_id
    INNER JOIN fact_payments p 
        ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY c.customer_unique_id, c.customer_state
),
ReferenceDate AS (
    SELECT MAX(order_purchase_timestamp) AS max_date FROM fact_orders
),
RFM_Calculated AS (
    SELECT 
        co.customer_unique_id,
        co.customer_state,
        co.total_orders AS frequency,
        co.total_monetary_spend AS monetary,
        co.avg_order_value,
        CAST(JULIANDAY(rd.max_date) - JULIANDAY(co.last_purchase_date) AS INTEGER) AS recency_days
    FROM CustomerOrders co
    CROSS JOIN ReferenceDate rd
)
SELECT 
    customer_unique_id,
    customer_state,
    recency_days,
    frequency,
    ROUND(monetary, 2) AS monetary_value,
    ROUND(avg_order_value, 2) AS avg_order_value,
    CASE 
        WHEN recency_days <= 90 THEN 'Active'
        WHEN recency_days <= 180 THEN 'At-Risk'
        ELSE 'Dormant'
    END AS recency_status,
    CASE 
        WHEN frequency > 1 THEN 'Repeat Buyer'
        ELSE 'One-Time Buyer'
    END AS buyer_type
FROM RFM_Calculated
ORDER BY monetary DESC;
