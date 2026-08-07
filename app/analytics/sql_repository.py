"""
Reusable SQLAlchemy ORM queries for analytics.

Contains query builders for extracting analytical datasets without embedded business logic.
"""

from typing import Any
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.domain import (
    CustomerModel,
    OrderItemModel,
    OrderModel,
    PaymentModel,
    ProductModel,
    ReviewModel,
)


class SQLRepository:
    """
    SQL Query repository providing standardized ORM queries for domain entities.
    """

    @staticmethod
    def query_customers() -> Select:
        """
        Build select query for all customer domain records.
        """
        return select(CustomerModel)

    @staticmethod
    def query_products() -> Select:
        """
        Build select query for all product domain records.
        """
        return select(ProductModel)

    @staticmethod
    def query_orders() -> Select:
        """
        Build select query for all order domain records.
        """
        return select(OrderModel)

    @staticmethod
    def query_order_items() -> Select:
        """
        Build select query for all order item domain records.
        """
        return select(OrderItemModel)

    @staticmethod
    def query_payments() -> Select:
        """
        Build select query for all payment domain records.
        """
        return select(PaymentModel)

    @staticmethod
    def query_reviews() -> Select:
        """
        Build select query for all review domain records.
        """
        return select(ReviewModel)

    @staticmethod
    def query_full_dataset() -> Select:
        """
        Build joined query for full analytical view joining orders, customers, items, products, payments, and reviews.
        """
        return (
            select(
                OrderModel,
                CustomerModel,
                OrderItemModel,
                ProductModel,
                PaymentModel,
                ReviewModel,
            )
            .join(CustomerModel, OrderModel.customer_id == CustomerModel.customer_id)
            .outerjoin(OrderItemModel, OrderModel.order_id == OrderItemModel.order_id)
            .outerjoin(ProductModel, OrderItemModel.product_id == ProductModel.product_id)
            .outerjoin(PaymentModel, OrderModel.order_id == PaymentModel.order_id)
            .outerjoin(ReviewModel, OrderModel.order_id == ReviewModel.order_id)
        )
