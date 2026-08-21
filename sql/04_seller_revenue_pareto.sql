-- ==============================================================================
-- Query 04: Seller Pareto Revenue Concentration (80/20 Rule)
-- Business Question: What proportion of sellers account for 80% of total marketplace revenue?
-- Key Techniques: Window Functions (SUM() OVER(), ROW_NUMBER() OVER()), Cumulative Ratio
-- ==============================================================================

WITH SellerRevenue AS (
    SELECT 
        s.seller_id,
        s.seller_state,
        COUNT(DISTINCT oi.order_id) AS total_orders_handled,
        SUM(oi.price) AS total_seller_revenue,
        AVG(oi.price) AS avg_item_price
    FROM fact_order_items oi
    INNER JOIN dim_sellers s 
        ON oi.seller_id = s.seller_id
    INNER JOIN fact_orders o 
        ON oi.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY s.seller_id, s.seller_state
),
RankedSellers AS (
    SELECT 
        seller_id,
        seller_state,
        total_orders_handled,
        ROUND(total_seller_revenue, 2) AS total_seller_revenue,
        ROUND(avg_item_price, 2) AS avg_item_price,
        ROW_NUMBER() OVER (ORDER BY total_seller_revenue DESC) AS seller_rank,
        COUNT(*) OVER () AS total_seller_count,
        SUM(total_seller_revenue) OVER () AS global_total_revenue,
        SUM(total_seller_revenue) OVER (ORDER BY total_seller_revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_seller_revenue
    FROM SellerRevenue
)
SELECT 
    seller_id,
    seller_state,
    seller_rank,
    total_orders_handled,
    total_seller_revenue,
    ROUND((CAST(seller_rank AS REAL) / total_seller_count) * 100.0, 2) AS cumulative_seller_pct,
    ROUND((cumulative_seller_revenue / global_total_revenue) * 100.0, 2) AS cumulative_revenue_pct,
    CASE 
        WHEN (cumulative_seller_revenue / global_total_revenue) <= 0.80 THEN 'Top 80% Revenue Driver'
        ELSE 'Long-Tail Contributor'
    END AS pareto_tier
FROM RankedSellers
ORDER BY seller_rank ASC;
