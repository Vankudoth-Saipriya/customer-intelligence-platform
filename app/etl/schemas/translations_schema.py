"""
Declarative dataset schema definition for Category Translations.
"""

from app.etl.schemas.base_schema import DatasetSchema

TRANSLATIONS_SCHEMA = DatasetSchema(
    name="translations",
    required_columns=[
        "product_category_name",
        "product_category_name_english",
    ],
    optional_columns=[],
    expected_dtypes={
        "product_category_name": "object",
        "product_category_name_english": "object",
    },
    primary_key="product_category_name",
    composite_keys=[],
    nullable_columns=[],
    enum_fields={},
    numeric_constraints={},
    date_fields=[],
)
