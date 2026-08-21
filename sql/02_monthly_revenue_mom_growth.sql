-- ==============================================================================
-- Query 02: Monthly Revenue Trajectory & Month-over-Month (MoM) Growth Rate
-- Business Question: What is our revenue growth rate over time, and what are peak sales months?
-- Key Techniques: Date Formatting, CTEs, Window Functions (LAG(), SUM() OVER())
-- ==============================================================================

WITH MonthlyAggregates AS (
    SELECT 
        STRFTIME('%Y-%m', o.order_purchase_timestamp) AS year_month,
        COUNT(DISTINCT o.order_id) AS total_orders,
        COUNT(DISTINCT c.customer_unique_id) AS unique_buyers,
        SUM(p.payment_value) AS monthly_revenue,
        AVG(p.payment_value) AS monthly_aov
    FROM fact_orders o
    INNER JOIN dim_customers c 
        ON o.customer_id = c.customer_id
    INNER JOIN fact_payments p 
        ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY STRFTIME('%Y-%m', o.order_purchase_timestamp)
),
MonthlyGrowth AS (
    SELECT 
        year_month,
        total_orders,
        unique_buyers,
        ROUND(monthly_revenue, 2) AS monthly_revenue,
        ROUND(monthly_aov, 2) AS monthly_aov,
        LAG(monthly_revenue, 1) OVER (ORDER BY year_month) AS prev_month_revenue,
        SUM(monthly_revenue) OVER (ORDER BY year_month ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_revenue
    FROM MonthlyAggregates
)
SELECT 
    year_month,
    total_orders,
    unique_buyers,
    monthly_revenue,
    monthly_aov,
    ROUND(cumulative_revenue, 2) AS cumulative_revenue,
    ROUND(
        CASE 
            WHEN prev_month_revenue IS NULL THEN 0.0
            ELSE ((monthly_revenue - prev_month_revenue) / prev_month_revenue) * 100.0
        END, 2
    ) AS mom_growth_pct
FROM MonthlyGrowth
ORDER BY year_month ASC;
