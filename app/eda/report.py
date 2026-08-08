"""
Exploratory Data Analysis (EDA) report data structures.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger


@dataclass
class CustomerAnalysisReport:
    """
    Structured report containing results of Customer Exploratory Data Analysis.
    """

    total_customers_analyzed: int
    geographic_distribution: Dict[str, Any] = field(default_factory=dict)
    growth_over_time: Dict[str, Any] = field(default_factory=dict)
    repeat_analysis: Dict[str, Any] = field(default_factory=dict)
    purchase_distribution: Dict[str, Any] = field(default_factory=dict)
    spending_overview: Dict[str, Any] = field(default_factory=dict)
    value_segmentation: Dict[str, Any] = field(default_factory=dict)
    frequency_segmentation: Dict[str, Any] = field(default_factory=dict)
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save CustomerAnalysisReport to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "eda"
            target_path = target_dir / "customer_analysis.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving CustomerAnalysisReport artifact to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Customer EDA report artifact: '{target_path.name}'")
        return target_path


@dataclass
class ProductAnalysisReport:
    """
    Structured report containing results of Product Exploratory Data Analysis.
    """

    total_products_analyzed: int
    category_analysis: Dict[str, Any] = field(default_factory=dict)
    dimension_analysis: Dict[str, Any] = field(default_factory=dict)
    product_performance: Dict[str, Any] = field(default_factory=dict)
    freight_analysis: Dict[str, Any] = field(default_factory=dict)
    translation_coverage: Dict[str, Any] = field(default_factory=dict)
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save ProductAnalysisReport to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "eda"
            target_path = target_dir / "product_analysis.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving ProductAnalysisReport artifact to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Product EDA report artifact: '{target_path.name}'")
        return target_path


@dataclass
class SalesAnalysisReport:
    """
    Structured report containing results of Sales Exploratory Data Analysis.
    """

    total_orders_analyzed: int
    revenue_analysis: Dict[str, Any] = field(default_factory=dict)
    order_analysis: Dict[str, Any] = field(default_factory=dict)
    seasonality: Dict[str, Any] = field(default_factory=dict)
    sales_performance: Dict[str, Any] = field(default_factory=dict)
    operational_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save SalesAnalysisReport to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "eda"
            target_path = target_dir / "sales_analysis.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving SalesAnalysisReport artifact to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Sales EDA report artifact: '{target_path.name}'")
        return target_path


@dataclass
class PaymentAnalysisReport:
    """
    Structured report containing results of Payment Exploratory Data Analysis.
    """

    total_payments_analyzed: int
    payment_method_analysis: Dict[str, Any] = field(default_factory=dict)
    installment_analysis: Dict[str, Any] = field(default_factory=dict)
    payment_value_analysis: Dict[str, Any] = field(default_factory=dict)
    payment_behavior: Dict[str, Any] = field(default_factory=dict)
    business_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save PaymentAnalysisReport to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "eda"
            target_path = target_dir / "payment_analysis.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving PaymentAnalysisReport artifact to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Payment EDA report artifact: '{target_path.name}'")
        return target_path


@dataclass
class DeliveryAnalysisReport:
    """
    Structured report containing results of Delivery Exploratory Data Analysis.
    """

    total_orders_analyzed: int
    total_delivered_orders: int
    delivery_time_analysis: Dict[str, Any] = field(default_factory=dict)
    delivery_delay_analysis: Dict[str, Any] = field(default_factory=dict)
    regional_delivery_performance: Dict[str, Any] = field(default_factory=dict)
    freight_and_logistics: Dict[str, Any] = field(default_factory=dict)
    operational_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save DeliveryAnalysisReport to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "eda"
            target_path = target_dir / "delivery_analysis.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving DeliveryAnalysisReport artifact to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Delivery EDA report artifact: '{target_path.name}'")
        return target_path


@dataclass
class ReviewAnalysisReport:
    """
    Structured report containing results of Review Exploratory Data Analysis.
    """

    total_reviews_analyzed: int
    review_score_analysis: Dict[str, Any] = field(default_factory=dict)
    review_text_analysis: Dict[str, Any] = field(default_factory=dict)
    customer_satisfaction: Dict[str, Any] = field(default_factory=dict)
    business_insights: Dict[str, Any] = field(default_factory=dict)
    operational_metrics: Dict[str, Any] = field(default_factory=dict)
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save ReviewAnalysisReport to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "eda"
            target_path = target_dir / "review_analysis.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Saving ReviewAnalysisReport artifact to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Review EDA report artifact: '{target_path.name}'")
        return target_path





