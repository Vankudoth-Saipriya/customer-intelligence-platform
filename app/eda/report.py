"""
Customer EDA report data structures.
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
