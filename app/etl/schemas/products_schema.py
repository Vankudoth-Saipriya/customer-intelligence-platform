"""
Declarative dataset schema definition for Products Catalog.
"""

from app.etl.schemas.base_schema import DatasetSchema, NumericConstraint

PRODUCTS_SCHEMA = DatasetSchema(
    name="products",
    required_columns=["product_id"],
    optional_columns=[
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    expected_dtypes={
        "product_id": "object",
        "product_category_name": "object",
        "product_name_lenght": "float64",
        "product_description_lenght": "float64",
        "product_photos_qty": "float64",
        "product_weight_g": "float64",
        "product_length_cm": "float64",
        "product_height_cm": "float64",
        "product_width_cm": "float64",
    },
    primary_key="product_id",
    composite_keys=[],
    nullable_columns=[
        "product_category_name",
        "product_name_lenght",
        "product_description_lenght",
        "product_photos_qty",
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm",
    ],
    enum_fields={},
    numeric_constraints={
        "product_name_lenght": NumericConstraint(min_value=0),
        "product_description_lenght": NumericConstraint(min_value=0),
        "product_photos_qty": NumericConstraint(min_value=0),
        "product_weight_g": NumericConstraint(min_value=0.0),
        "product_length_cm": NumericConstraint(min_value=0.0),
        "product_height_cm": NumericConstraint(min_value=0.0),
        "product_width_cm": NumericConstraint(min_value=0.0),
    },
    date_fields=[],
)
