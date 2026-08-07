"""
DatasetType enumeration module for strong typing of dataset identifiers across the ETL pipeline.
"""

from enum import Enum


class DatasetType(str, Enum):
    """
    Enumeration of supported dataset identifiers.
    """

    CUSTOMERS = "customers"
    ORDERS = "orders"
    ORDER_ITEMS = "order_items"
    PRODUCTS = "products"
    PAYMENTS = "payments"
    REVIEWS = "reviews"
    TRANSLATIONS = "translations"

    def __str__(self) -> str:
        return self.value
