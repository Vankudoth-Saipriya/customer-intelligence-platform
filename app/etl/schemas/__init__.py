"""
ETL Schemas Package.

Exposes declarative dataset schema definitions for consuming validators.
"""

from app.etl.schemas.base_schema import DatasetSchema, NumericConstraint
from app.etl.schemas.customers_schema import CUSTOMERS_SCHEMA
from app.etl.schemas.order_items_schema import ORDER_ITEMS_SCHEMA
from app.etl.schemas.orders_schema import ORDERS_SCHEMA
from app.etl.schemas.payments_schema import PAYMENTS_SCHEMA
from app.etl.schemas.products_schema import PRODUCTS_SCHEMA
from app.etl.schemas.reviews_schema import REVIEWS_SCHEMA
from app.etl.schemas.translations_schema import TRANSLATIONS_SCHEMA

from app.etl.schemas.schema_registry import SchemaRegistry, schema_registry

__all__ = [
    "DatasetSchema",
    "NumericConstraint",
    "CUSTOMERS_SCHEMA",
    "ORDERS_SCHEMA",
    "ORDER_ITEMS_SCHEMA",
    "PRODUCTS_SCHEMA",
    "PAYMENTS_SCHEMA",
    "REVIEWS_SCHEMA",
    "TRANSLATIONS_SCHEMA",
    "SchemaRegistry",
    "schema_registry",
]
