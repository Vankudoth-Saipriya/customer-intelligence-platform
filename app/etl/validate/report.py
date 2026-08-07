"""
Validation result, check, severity, report, and summary data structures.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from app.etl.utils.dataset_types import DatasetType


class ValidationResult(str, Enum):
    """
    Validation outcome status enumeration.
    """

    PASSED = "PASSED"
    FAILED = "FAILED"
    WARNING = "WARNING"

    def __str__(self) -> str:
        return self.value


class ValidationSeverity(str, Enum):
    """
    Validation check severity classification.
    """

    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def __str__(self) -> str:
        return self.value


@dataclass
class ValidationCheck:
    """
    Individual validation check result container.
    """

    check_name: str
    status: ValidationResult
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    details: Optional[Dict[str, Any]] = None


@dataclass
class ValidationReport:
    """
    Validation evaluation report for a single dataset.
    """

    dataset: DatasetType
    total_rows: int
    status: ValidationResult
    passed_checks: List[str] = field(default_factory=list)
    failed_checks: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checks: List[ValidationCheck] = field(default_factory=list)
    execution_time_sec: float = 0.0
    statistics: Dict[str, Any] = field(default_factory=dict)
    invalid_row_indices: List[int] = field(default_factory=list)

    @property
    def info_count(self) -> int:
        """
        Count of non-passed INFO checks.
        """
        return sum(
            1 for c in self.checks
            if c.severity == ValidationSeverity.INFO and c.status != ValidationResult.PASSED
        )

    @property
    def warning_count(self) -> int:
        """
        Count of non-passed WARNING checks.
        """
        return sum(
            1 for c in self.checks
            if c.severity == ValidationSeverity.WARNING and c.status != ValidationResult.PASSED
        )

    @property
    def error_count(self) -> int:
        """
        Count of non-passed ERROR checks.
        """
        return sum(
            1 for c in self.checks
            if c.severity == ValidationSeverity.ERROR and c.status != ValidationResult.PASSED
        )

    @property
    def critical_count(self) -> int:
        """
        Count of non-passed CRITICAL checks.
        """
        return sum(
            1 for c in self.checks
            if c.severity == ValidationSeverity.CRITICAL and c.status != ValidationResult.PASSED
        )

    def has_errors(self) -> bool:
        """
        Check if any ERROR or CRITICAL validation failures exist.
        """
        return self.error_count > 0 or self.critical_count > 0

    def has_critical(self) -> bool:
        """
        Check if any CRITICAL validation failures exist.
        """
        return self.critical_count > 0

    def can_continue(self) -> bool:
        """
        Determine if processing can continue (returns False if any CRITICAL validation fails).
        """
        return not self.has_critical()

    @property
    def is_valid(self) -> bool:
        """
        Check if dataset validation passed cleanly without errors or critical issues.
        """
        return self.can_continue() and not self.has_errors()


@dataclass
class ValidationSummary:
    """
    Aggregated validation report summary across an entire ETL batch run.
    """

    reports: Dict[DatasetType, ValidationReport] = field(default_factory=dict)
    total_datasets: int = 0
    passed_datasets: int = 0
    failed_datasets: int = 0
    overall_status: ValidationResult = ValidationResult.PASSED
    total_execution_time_sec: float = 0.0

    def has_errors(self) -> bool:
        """
        Check if any dataset report contains ERROR or CRITICAL failures.
        """
        return any(r.has_errors() for r in self.reports.values())

    def has_critical(self) -> bool:
        """
        Check if any dataset report contains CRITICAL failures.
        """
        return any(r.has_critical() for r in self.reports.values())

    def can_continue(self) -> bool:
        """
        Determine if batch execution can continue (returns False if any CRITICAL failure exists).
        """
        return not self.has_critical()

    @property
    def is_valid(self) -> bool:
        """
        Check if overall batch validation succeeded.
        """
        return self.can_continue() and not self.has_errors()
