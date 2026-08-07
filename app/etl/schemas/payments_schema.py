"""
Declarative dataset schema definition for Payments.
"""

from app.etl.schemas.base_schema import DatasetSchema, NumericConstraint

PAYMENTS_SCHEMA = DatasetSchema(
    name="payments",
    required_columns=[
        "order_id",
        "payment_sequential",
        "payment_type",
        "payment_installments",
        "payment_value",
    ],
    optional_columns=[],
    expected_dtypes={
        "order_id": "object",
        "payment_sequential": "int64",
        "payment_type": "object",
        "payment_installments": "int64",
        "payment_value": "float64",
    },
    primary_key=None,
    composite_keys=["order_id", "payment_sequential"],
    nullable_columns=[],
    enum_fields={
        "payment_type": [
            "credit_card",
            "boleto",
            "voucher",
            "debit_card",
            "not_defined",
        ]
    },
    numeric_constraints={
        "payment_sequential": NumericConstraint(min_value=1),
        "payment_installments": NumericConstraint(min_value=0),
        "payment_value": NumericConstraint(min_value=0.0),
    },
    date_fields=[],
)
