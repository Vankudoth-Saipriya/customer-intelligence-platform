-- ==============================================================================
-- Query 05: Delivery SLA Achievement & Regional State Performance Ranking
-- Business Question: Which Brazilian states experience the highest logistics delays and SLA breaches?
-- Key Techniques: Date Arithmetic (JULIANDAY), CASE WHEN SLA flags, Window Functions (ROW_NUMBER(), NTILE())
-- ==============================================================================

WITH OrderFulfillment AS (
    SELECT 
        o.order_id,
        c.customer_state,
        c.customer_city,
        o.order_purchase_timestamp,
        o.order_delivered_customer_date,
        o.order_estimated_delivery_date,
        CAST(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_purchase_timestamp) AS REAL) AS actual_delivery_days,
        CAST(JULIANDAY(o.order_delivered_customer_date) - JULIANDAY(o.order_estimated_delivery_date) AS REAL) AS delay_days
    FROM fact_orders o
    INNER JOIN dim_customers c 
        ON o.customer_id = c.customer_id
    WHERE o.order_status = 'delivered'
        AND o.order_delivered_customer_date IS NOT NULL
),
StateLogisticsAggregates AS (
    SELECT 
        customer_state,
        COUNT(order_id) AS total_delivered_orders,
        ROUND(AVG(actual_delivery_days), 1) AS avg_delivery_days,
        ROUND(AVG(delay_days), 1) AS avg_delay_days,
        SUM(CASE WHEN delay_days > 0 THEN 1 ELSE 0 END) AS late_deliveries_count,
        SUM(CASE WHEN delay_days <= 0 THEN 1 ELSE 0 END) AS ontime_deliveries_count
    FROM OrderFulfillment
    GROUP BY customer_state
)
SELECT 
    customer_state,
    total_delivered_orders,
    avg_delivery_days,
    avg_delay_days,
    late_deliveries_count,
    ROUND((CAST(ontime_deliveries_count AS REAL) / total_delivered_orders) * 100.0, 2) AS sla_achievement_rate_pct,
    ROW_NUMBER() OVER (ORDER BY (CAST(ontime_deliveries_count AS REAL) / total_delivered_orders) DESC) AS sla_rank_best_to_worst,
    NTILE(4) OVER (ORDER BY avg_delivery_days ASC) AS speed_quartile
FROM StateLogisticsAggregates
WHERE total_delivered_orders >= 100
ORDER BY sla_rank_best_to_worst ASC;
