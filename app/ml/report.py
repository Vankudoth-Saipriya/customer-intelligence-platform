"""
Customer Segmentation Report & Metadata Data Structures.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger


@dataclass
class CustomerSegmentationReport:
    """
    Structured report containing metadata and performance metrics of Customer Segmentation.
    """

    total_customers_segmented: int
    best_k: int
    best_silhouette_score: float
    model_evaluation_metrics: Dict[str, Dict[str, float]] = field(default_factory=dict)
    cluster_profiles: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    csv_path: str = ""
    parquet_path: str = ""
    metadata_path: str = ""
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save CustomerSegmentationReport metadata to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "ml"
            target_path = target_dir / "customer_segmentation_metadata.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path = str(target_path.resolve())

        logger.info(f"Saving CustomerSegmentationReport metadata to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Segmentation metadata artifact: '{target_path.name}'")
        return target_path


@dataclass
class CustomerCLVReport:
    """
    Structured report containing metadata and performance evaluation of CLV Prediction models.
    """

    total_customers: int
    best_model_name: str
    best_r2_score: float
    best_rmse: float
    best_mae: float
    best_median_ae: float = 0.0
    best_non_zero_clv_mae: float = 0.0
    model_comparison: Dict[str, Dict[str, float]] = field(default_factory=dict)
    feature_importance: List[Dict[str, Any]] = field(default_factory=list)
    csv_path: str = ""
    parquet_path: str = ""
    metadata_path: str = ""
    training_time_sec: float = 0.0
    prediction_time_sec: float = 0.0
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save CustomerCLVReport metadata to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "ml"
            target_path = target_dir / "customer_clv_metadata.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path = str(target_path.resolve())

        logger.info(f"Saving CustomerCLVReport metadata to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated CLV Prediction metadata artifact: '{target_path.name}'")
        return target_path


@dataclass
class RepeatPurchasePredictionReport:
    """
    Structured report containing metadata and classification metrics of Repeat Purchase Propensity models.
    """

    total_customers: int
    class_distribution: Dict[str, int] = field(default_factory=dict)
    best_model_name: str = ""
    best_roc_auc: float = 0.0
    best_f1_score: float = 0.0
    best_accuracy: float = 0.0
    best_precision: float = 0.0
    best_recall: float = 0.0
    best_pr_auc: float = 0.0
    optimal_threshold: float = 0.5
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    confusion_matrix: Dict[str, Any] = field(default_factory=dict)
    model_comparison: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    feature_importance: List[Dict[str, Any]] = field(default_factory=list)
    csv_path: str = ""
    parquet_path: str = ""
    metadata_path: str = ""
    training_time_sec: float = 0.0
    prediction_time_sec: float = 0.0
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save RepeatPurchasePredictionReport metadata to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "ml"
            target_path = target_dir / "repeat_purchase_metadata.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path = str(target_path.resolve())

        logger.info(f"Saving RepeatPurchasePredictionReport metadata to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Repeat Purchase metadata artifact: '{target_path.name}'")
        return target_path


