"""
Customer Feature Store Report & Metadata Data Structures.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from loguru import logger


@dataclass
class CustomerFeatureStoreReport:
    """
    Structured metadata report containing summary of generated Customer Feature Store.
    """

    total_customers: int
    total_features: int
    feature_groups: Dict[str, List[str]] = field(default_factory=dict)
    parquet_path: str = ""
    csv_path: str = ""
    metadata_path: str = ""
    column_types: Dict[str, str] = field(default_factory=dict)
    execution_time_sec: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert report object to dictionary.
        """
        return asdict(self)

    def save_json(self, output_path: Optional[Path] = None) -> Path:
        """
        Save CustomerFeatureStoreReport metadata to JSON artifact.
        """
        if output_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "features"
            target_path = target_dir / "customer_feature_store_metadata.json"
        else:
            target_path = Path(output_path)

        target_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path = str(target_path.resolve())

        logger.info(f"Saving CustomerFeatureStoreReport metadata to: '{target_path.resolve()}'")

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

        logger.info(f"Successfully generated Feature Store metadata artifact: '{target_path.name}'")
        return target_path
