"""
Declarative dataset schema definition for Customer Reviews.
"""

from app.etl.schemas.base_schema import DatasetSchema, NumericConstraint

REVIEWS_SCHEMA = DatasetSchema(
    name="reviews",
    required_columns=[
        "review_id",
        "order_id",
        "review_score",
        "review_creation_date",
        "review_answer_timestamp",
    ],
    optional_columns=[
        "review_comment_title",
        "review_comment_message",
    ],
    expected_dtypes={
        "review_id": "object",
        "order_id": "object",
        "review_score": "int64",
        "review_comment_title": "object",
        "review_comment_message": "object",
        "review_creation_date": "object",
        "review_answer_timestamp": "object",
    },
    primary_key=None,
    composite_keys=["review_id", "order_id"],
    nullable_columns=[
        "review_comment_title",
        "review_comment_message",
    ],
    enum_fields={},
    numeric_constraints={
        "review_score": NumericConstraint(min_value=1, max_value=5)
    },
    date_fields=[
        "review_creation_date",
        "review_answer_timestamp",
    ],
)
