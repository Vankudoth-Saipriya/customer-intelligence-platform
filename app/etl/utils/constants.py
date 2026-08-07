"""
Constants and enumerations for the ETL pipeline.
"""

from typing import Dict, List

# Raw CSV File Names
RAW_CUSTOMERS_CSV: str = "olist_customers_dataset.csv"
RAW_GEOLOCATION_CSV: str = "olist_geolocation_dataset.csv"
RAW_ORDER_ITEMS_CSV: str = "olist_order_items_dataset.csv"
RAW_ORDER_PAYMENTS_CSV: str = "olist_order_payments_dataset.csv"
RAW_ORDER_REVIEWS_CSV: str = "olist_order_reviews_dataset.csv"
RAW_ORDERS_CSV: str = "olist_orders_dataset.csv"
RAW_PRODUCTS_CSV: str = "olist_products_dataset.csv"
RAW_SELLERS_CSV: str = "olist_sellers_dataset.csv"
RAW_TRANSLATIONS_CSV: str = "product_category_name_translation.csv"

RAW_DATASETS: List[str] = [
    RAW_CUSTOMERS_CSV,
    RAW_GEOLOCATION_CSV,
    RAW_ORDER_ITEMS_CSV,
    RAW_ORDER_PAYMENTS_CSV,
    RAW_ORDER_REVIEWS_CSV,
    RAW_ORDERS_CSV,
    RAW_PRODUCTS_CSV,
    RAW_SELLERS_CSV,
    RAW_TRANSLATIONS_CSV,
]

# Database Target Table Names
TABLE_CUSTOMERS: str = "customers"
TABLE_PRODUCTS: str = "products"
TABLE_ORDERS: str = "orders"
TABLE_ORDER_ITEMS: str = "order_items"
TABLE_PAYMENTS: str = "payments"
TABLE_REVIEWS: str = "reviews"

TABLE_NAMES: List[str] = [
    TABLE_CUSTOMERS,
    TABLE_PRODUCTS,
    TABLE_ORDERS,
    TABLE_ORDER_ITEMS,
    TABLE_PAYMENTS,
    TABLE_REVIEWS,
]

# Execution Constants
DEFAULT_BATCH_CHUNK_SIZE: int = 10000
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_ERROR_THRESHOLD_PERCENT: float = 5.0
