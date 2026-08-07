"""
Load report and summary data structures for database ingestion reporting.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from app.etl.utils.dataset_types import DatasetType


@dataclass
class LoadReport:
    """
    Ingestion load evaluation report for a single dataset.
    """

    dataset: DatasetType
    rows_attempted: int
    rows_inserted: int
    rows_skipped: int = 0
    execution_time_sec: float = 0.0
    verified: bool = False
    verification_message: str = ""
    verification_time_sec: float = 0.0
    warnings: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """
        Calculate percentage of rows successfully inserted.
        """
        if self.rows_attempted == 0:
            return 100.0
        return round((self.rows_inserted / self.rows_attempted) * 100.0, 2)

    def is_verified(self) -> bool:
        """
        Check if post-load verification succeeded for this dataset.
        """
        return self.verified


@dataclass
class LoadSummary:
    """
    Aggregated database load summary across an entire ETL batch run.
    """

    reports: Dict[DatasetType, LoadReport] = field(default_factory=dict)
    total_datasets: int = 0
    total_attempted: int = 0
    total_inserted: int = 0
    total_skipped: int = 0
    total_execution_time_sec: float = 0.0

    def is_verified(self) -> bool:
        """
        Check if all loaded datasets passed post-load verification.
        """
        return all(r.is_verified() for r in self.reports.values())
