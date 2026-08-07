"""
Declarative dataset schema definition for Customers.
"""

from app.etl.schemas.base_schema import DatasetSchema, NumericConstraint

CUSTOMERS_SCHEMA = DatasetSchema(
    name="customers",
    required_columns=[
        "customer_id",
        "customer_unique_id",
        "customer_zip_code_prefix",
        "customer_city",
        "customer_state",
    ],
    optional_columns=[],
    expected_dtypes={
        "customer_id": "object",
        "customer_unique_id": "object",
        "customer_zip_code_prefix": "int64",
        "customer_city": "object",
        "customer_state": "object",
    },
    primary_key="customer_id",
    composite_keys=[],
    nullable_columns=[],
    enum_fields={
        "customer_state": [
            "AC",
            "AL",
            "AM",
            "AP",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MG",
            "MS",
            "MT",
            "PA",
            "PB",
            "PE",
            "PI",
            "PR",
            "RJ",
            "RN",
            "RO",
            "RR",
            "RS",
            "SC",
            "SE",
            "SP",
            "TO",
        ]
    },
    numeric_constraints={
        "customer_zip_code_prefix": NumericConstraint(min_value=0, max_value=99999)
    },
    date_fields=[],
)
