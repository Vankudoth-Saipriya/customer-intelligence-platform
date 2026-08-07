"""
Declarative dataset schema definition for Order Items.
"""

from app.etl.schemas.base_schema import DatasetSchema, NumericConstraint

ORDER_ITEMS_SCHEMA = DatasetSchema(
    name="order_items",
    required_columns=[
        "order_id",
        "order_item_id",
        "product_id",
        "seller_id",
        "shipping_limit_date",
        "price",
        "freight_value",
    ],
    optional_columns=[],
    expected_dtypes={
        "order_id": "object",
        "order_item_id": "int64",
        "product_id": "object",
        "seller_id": "object",
        "shipping_limit_date": "object",
        "price": "float64",
        "freight_value": "float64",
    },
    primary_key=None,
    composite_keys=["order_id", "order_item_id"],
    nullable_columns=[],
    enum_fields={},
    numeric_constraints={
        "order_item_id": NumericConstraint(min_value=1),
        "price": NumericConstraint(min_value=0.0),
        "freight_value": NumericConstraint(min_value=0.0),
    },
    date_fields=["shipping_limit_date"],
)
