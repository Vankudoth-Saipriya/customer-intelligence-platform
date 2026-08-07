"""
Transformation step, report, and summary data structures for transformation auditing.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List
from app.etl.utils.dataset_types import DatasetType


@dataclass
class TransformationStep:
    """
    Detailed audit log step for an individual data transformation operation.
    """

    step_name: str
    description: str
    affected_rows: int
    columns_modified: List[str]
    execution_time_ms: float
    status: str = "SUCCESS"  # SUCCESS, WARNING, FAILED


@dataclass
class TransformationReport:
    """
    Transformation execution report for a single dataset.
    """

    dataset: DatasetType
    rows_processed: int
    transformations_applied: List[str] = field(default_factory=list)
    steps: List[TransformationStep] = field(default_factory=list)
    execution_time_sec: float = 0.0
    warnings: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)

    def total_rows_modified(self) -> int:
        """
        Calculate total count of affected/modified rows across all transformation steps.
        """
        return sum(step.affected_rows for step in self.steps)

    def total_execution_time(self) -> float:
        """
        Calculate total execution time in seconds.
        """
        if self.execution_time_sec > 0:
            return self.execution_time_sec
        return sum(step.execution_time_ms for step in self.steps) / 1000.0

    def summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary dictionary of the transformation report.
        """
        dataset_name = (
            self.dataset.value if isinstance(self.dataset, DatasetType) else str(self.dataset)
        )
        return {
            "dataset": dataset_name,
            "rows_processed": self.rows_processed,
            "total_steps": len(self.steps),
            "total_rows_modified": self.total_rows_modified(),
            "total_execution_time_sec": round(self.total_execution_time(), 4),
            "warnings_count": len(self.warnings),
            "transformations": self.transformations_applied,
            "statistics": self.statistics,
        }


@dataclass
class TransformationSummary:
    """
    Aggregated transformation summary across an entire ETL batch run.
    """

    reports: Dict[DatasetType, TransformationReport] = field(default_factory=dict)
    total_datasets: int = 0
    total_execution_time_sec: float = 0.0
