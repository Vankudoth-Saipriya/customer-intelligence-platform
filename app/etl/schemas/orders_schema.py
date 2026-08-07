"""
Declarative dataset schema definition for Orders.
"""

from app.etl.schemas.base_schema import DatasetSchema

ORDERS_SCHEMA = DatasetSchema(
    name="orders",
    required_columns=[
        "order_id",
        "customer_id",
        "order_status",
        "order_purchase_timestamp",
        "order_estimated_delivery_date",
    ],
    optional_columns=[
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
    ],
    expected_dtypes={
        "order_id": "object",
        "customer_id": "object",
        "order_status": "object",
        "order_purchase_timestamp": "object",
        "order_approved_at": "object",
        "order_delivered_carrier_date": "object",
        "order_delivered_customer_date": "object",
        "order_estimated_delivery_date": "object",
    },
    primary_key="order_id",
    composite_keys=[],
    nullable_columns=[
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
    ],
    enum_fields={
        "order_status": [
            "created",
            "approved",
            "processing",
            "invoiced",
            "shipped",
            "delivered",
            "unavailable",
            "canceled",
        ]
    },
    numeric_constraints={},
    date_fields=[
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
)
