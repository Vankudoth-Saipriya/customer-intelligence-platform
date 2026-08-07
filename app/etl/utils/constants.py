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

REQUIRED_COLUMNS: Dict[str, List[str]] = {
    RAW_CUSTOMERS_CSV: [
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    RAW_GEOLOCATION_CSV: [
        "geolocation_zip_code_prefix",
        "geolocation_lat",
        "geolocation_lng",
        "geolocation_city",
        "geolocation_state",
    ],
    RAW_ORDER_ITEMS_CSV: [
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    RAW_ORDER_PAYMENTS_CSV: [
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    RAW_ORDER_REVIEWS_CSV: [
        "review_id",
        "order_id",
        "review_score",
        "review_comment_title",
        "review_comment_message",
        "review_creation_date",
        "review_answer_timestamp",
    ],
    RAW_ORDERS_CSV: [
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    RAW_PRODUCTS_CSV: [
        "product_id",
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    RAW_SELLERS_CSV: [
        "seller_id",
        "seller_zip_code_prefix",
        "seller_city",
        "seller_state",
    ],
    RAW_TRANSLATIONS_CSV: [
        "product_category_name",
        "product_category_name_english",
    ],
}

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
