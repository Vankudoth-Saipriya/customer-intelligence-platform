"""
Base schema models and constraint dataclasses for dataset validation.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class NumericConstraint:
    """
    Min/max numerical boundary constraints for dataset columns.
    """

    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allow_zero: bool = True


@dataclass(frozen=True)
class DatasetSchema:
    """
    Declarative schema definition for dataset validation and quality enforcement.
    """

    name: str
    required_columns: List[str] = field(default_factory=list)
    optional_columns: List[str] = field(default_factory=list)
    expected_dtypes: Dict[str, str] = field(default_factory=dict)
    primary_key: Optional[str] = None
    composite_keys: List[str] = field(default_factory=list)
    nullable_columns: List[str] = field(default_factory=list)
    enum_fields: Dict[str, List[str]] = field(default_factory=dict)
    numeric_constraints: Dict[str, NumericConstraint] = field(default_factory=dict)
    date_fields: List[str] = field(default_factory=list)
