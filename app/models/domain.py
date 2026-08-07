"""
SQLAlchemy 2.0 ORM domain models for the Customer Intelligence Platform.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class CustomerModel(Base):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_unique_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    customer_zip_code_prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    customer_city: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)


class ProductModel(Base):
    __tablename__ = "products"

    product_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_category_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category_name_english: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    product_name_lenght: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_description_lenght: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_photos_qty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_weight_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    product_length_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    product_height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    product_width_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    product_volume_cm3: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    volumetric_weight_g: Mapped[Optional[float]] = mapped_column(Float, nullable=True)


class OrderModel(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64), ForeignKey("customers.customer_id"), nullable=False, index=True)
    order_status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    order_purchase_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    order_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    order_delivered_carrier_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    order_delivered_customer_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    order_estimated_delivery_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Operational ETL Derived Fields
    order_items_qty: Mapped[int] = mapped_column(Integer, default=0)
    total_items_price: Mapped[float] = mapped_column(Float, default=0.0)
    total_freight_value: Mapped[float] = mapped_column(Float, default=0.0)
    order_value: Mapped[float] = mapped_column(Float, default=0.0)
    fulfillment_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delivery_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    delivery_delay_days: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    is_late_delivery: Mapped[bool] = mapped_column(Boolean, default=False)


class OrderItemModel(Base):
    __tablename__ = "order_items"

    order_id: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_id"), primary_key=True)
    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), ForeignKey("products.product_id"), nullable=False, index=True)
    seller_id: Mapped[str] = mapped_column(String(64), nullable=False)
    shipping_limit_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    freight_value: Mapped[float] = mapped_column(Float, nullable=False)


class PaymentModel(Base):
    __tablename__ = "payments"

    order_id: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_id"), primary_key=True)
    payment_sequential: Mapped[int] = mapped_column(Integer, primary_key=True)
    payment_type: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_installments: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_value: Mapped[float] = mapped_column(Float, nullable=False)
    is_installment_payment: Mapped[bool] = mapped_column(Boolean, default=False)
    is_voucher_payment: Mapped[bool] = mapped_column(Boolean, default=False)


class ReviewModel(Base):
    __tablename__ = "reviews"

    review_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(64), ForeignKey("orders.order_id"), primary_key=True, index=True)
    review_score: Mapped[int] = mapped_column(Integer, nullable=False)
    review_comment_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    review_comment_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_creation_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    review_answer_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    has_comment_title: Mapped[bool] = mapped_column(Boolean, default=False)
    has_comment_message: Mapped[bool] = mapped_column(Boolean, default=False)
