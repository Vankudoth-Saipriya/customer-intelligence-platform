-- ==============================================================================
-- Query 06: Data Quality Audit — Order Status Breakdown & Revenue Reconciliation
-- Business Question: What is the discrepancy between Gross GMV and Net Delivered Revenue, 
--                    and how do cancellation rates vary across customer states?
-- Key Techniques: Multi-table JOINs, CASE WHEN status flags, GROUP BY aggregations, Window Functions
-- ==============================================================================

WITH OrderStatusAggregates AS (
    SELECT 
        o.order_status,
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(DISTINCT o.customer_id) AS unique_customers,
        SUM(p.payment_value) AS gross_payment_value
    FROM fact_orders o
    LEFT JOIN fact_payments p 
        ON o.order_id = p.order_id
    GROUP BY o.order_status
),
RevenueReconciliation AS (
    SELECT 
        SUM(gross_payment_value) AS gross_gmv_all_orders,
        SUM(CASE WHEN order_status = 'delivered' THEN gross_payment_value ELSE 0 END) AS net_delivered_revenue,
        SUM(CASE WHEN order_status IN ('canceled', 'unavailable') THEN gross_payment_value ELSE 0 END) AS lost_canceled_revenue,
        SUM(CASE WHEN order_status NOT IN ('delivered', 'canceled', 'unavailable') THEN gross_payment_value ELSE 0 END) AS in_flight_order_revenue,
        SUM(CASE WHEN order_status = 'delivered' THEN 1 ELSE 0 END) AS delivered_orders_count,
        SUM(CASE WHEN order_status = 'canceled' THEN 1 ELSE 0 END) AS canceled_orders_count,
        SUM(CASE WHEN order_status = 'unavailable' THEN 1 ELSE 0 END) AS unavailable_orders_count,
        COUNT(*) AS total_order_records
    FROM OrderStatusAggregates
),
StateCancellationRates AS (
    SELECT 
        c.customer_state,
        COUNT(DISTINCT o.order_id) AS state_total_orders,
        SUM(CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END) AS state_canceled_orders,
        SUM(CASE WHEN o.order_status = 'delivered' THEN 1 ELSE 0 END) AS state_delivered_orders,
        ROUND((CAST(SUM(CASE WHEN o.order_status = 'canceled' THEN 1 ELSE 0 END) AS REAL) / COUNT(DISTINCT o.order_id)) * 100.0, 2) AS cancellation_rate_pct
    FROM fact_orders o
    INNER JOIN dim_customers c 
        ON o.customer_id = c.customer_id
    GROUP BY c.customer_state
)
SELECT 
    scr.customer_state,
    scr.state_total_orders,
    scr.state_delivered_orders,
    scr.state_canceled_orders,
    scr.cancellation_rate_pct,
    ROW_NUMBER() OVER (ORDER BY scr.cancellation_rate_pct DESC) AS cancellation_risk_rank
FROM StateCancellationRates scr
WHERE scr.state_total_orders >= 100
ORDER BY cancellation_risk_rank ASC;
