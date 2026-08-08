"""
Pydantic v2 schemas for ML Inference API.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerFeaturePayload(BaseModel):
    """
    Input schema for customer feature payload used across ML inference endpoints.
    """

    model_config = ConfigDict(extra="ignore")

    customer_id: Optional[str] = Field(default=None, description="Customer ID or Unique ID for direct lookup")
    customer_unique_id: Optional[str] = Field(default=None, description="Customer Unique ID")
    state: str = Field(default="SP", description="Customer State")
    city: str = Field(default="sao paulo", description="Customer City")
    customer_age_days: float = Field(default=100.0, description="Tenure in days since first purchase")
    recency_days: float = Field(default=30.0, description="Days since last purchase")
    frequency_orders: int = Field(default=1, description="Total order count")
    monetary_value: float = Field(default=150.0, description="Total monetary spend")
    avg_order_value: float = Field(default=150.0, description="Average order value")
    total_items: int = Field(default=1, description="Total items purchased")
    avg_items_per_order: float = Field(default=1.0, description="Average items per order")
    favorite_product_category: str = Field(default="bed_bath_table", description="Favorite product category")
    unique_categories: int = Field(default=1, description="Count of unique categories purchased")
    repeat_purchase_rate: float = Field(default=0.0, description="Repeat purchase rate")
    preferred_payment_method: str = Field(default="credit_card", description="Preferred payment method")
    avg_payment_value: float = Field(default=150.0, description="Average payment value")
    avg_installments: float = Field(default=2.0, description="Average payment installments")
    installment_ratio: float = Field(default=1.0, description="Ratio of installment payments")
    voucher_usage_ratio: float = Field(default=0.0, description="Ratio of voucher payments")
    avg_delivery_days: float = Field(default=10.0, description="Average delivery days")
    avg_delivery_delay: float = Field(default=-5.0, description="Average delivery delay days")
    late_delivery_ratio: float = Field(default=0.0, description="Late delivery ratio")
    avg_freight_value: float = Field(default=15.0, description="Average freight value")
    avg_review_score: float = Field(default=4.5, description="Average review rating")
    positive_review_ratio: float = Field(default=1.0, description="Positive review ratio")
    negative_review_ratio: float = Field(default=0.0, description="Negative review ratio")
    review_count: int = Field(default=1, description="Review count")
    total_revenue: float = Field(default=150.0, description="Total revenue")
    revenue_rank_percentile: float = Field(default=50.0, description="Revenue rank percentile")
    customer_value_tier: str = Field(default="Medium Value", description="Customer value tier")
    days_between_orders_mean: float = Field(default=0.0, description="Mean days between orders")
    order_value_std: float = Field(default=0.0, description="Order value standard deviation")
    spending_velocity: float = Field(default=45.0, description="Spending velocity per month")
    order_frequency_per_month: float = Field(default=0.3, description="Order frequency per month")


class SegmentationResponse(BaseModel):
    """
    Response schema for Customer Segmentation inference.
    """

    cluster_id: int = Field(description="Assigned cluster ID")
    cluster_name: str = Field(description="Cluster category name")
    business_description: str = Field(description="Business description of segment")


class CLVResponse(BaseModel):
    """
    Response schema for Customer Lifetime Value prediction inference.
    """

    predicted_clv: float = Field(description="Predicted customer lifetime value (revenue)")


class RepeatPurchaseResponse(BaseModel):
    """
    Response schema for Repeat Purchase Propensity inference.
    """

    repeat_purchase_probability: float = Field(description="Probability of repeat purchase (0.0 to 1.0)")
    predicted_repeat_customer: int = Field(description="Binary repeat purchase prediction (1 or 0)")


class ModelMetadataInfo(BaseModel):
    """
    Schema for model metadata info.
    """

    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    model_type: str
    feature_count: int
    training_date: str
    metrics: Dict[str, Any]
    status: str


class ModelsInfoResponse(BaseModel):
    """
    Response schema for GET /api/v1/ml/models
    """

    models: Dict[str, ModelMetadataInfo]


class MLHealthResponse(BaseModel):
    """
    Response schema for GET /api/v1/ml/health
    """

    status: str
    version: str
    inference_available: bool
    loaded_models: List[str]
