"""
ETL Validation Engine for validating single datasets and full ETL batch runs.

Utilizes SchemaRegistry definitions and executes generic as well as dataset-specific
validation rules to generate comprehensive ValidationReports and ValidationSummaries.
"""

import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from loguru import logger
import pandas as pd

from app.etl.config import ETLSettings, etl_settings
from app.etl.schemas.base_schema import DatasetSchema, NumericConstraint
from app.etl.schemas.schema_registry import SchemaRegistry, schema_registry
from app.etl.utils.dataset_types import DatasetType
from app.etl.utils.exceptions import CircuitBreakerTriggeredError, ETLValidationError
from app.etl.validate.report import (
    ValidationCheck,
    ValidationReport,
    ValidationResult,
    ValidationSeverity,
    ValidationSummary,
)


class Validator:
    """
    Validation engine evaluating pandas DataFrames against declarative dataset schemas.
    """

    def __init__(
        self,
        registry: Optional[SchemaRegistry] = None,
        settings: Optional[ETLSettings] = None,
    ) -> None:
        """
        Initialize Validator engine with SchemaRegistry and ETLSettings.

        Args:
            registry: SchemaRegistry instance. Defaults to global schema_registry.
            settings: ETL configuration instance. Defaults to application etl_settings.
        """
        self.registry = registry or schema_registry
        self.settings = settings or etl_settings

    def _resolve_dataset_type(self, dataset: Union[DatasetType, str]) -> DatasetType:
        """
        Resolve string or DatasetType enum to a DatasetType enum instance.
        """
        if isinstance(dataset, DatasetType):
            return dataset
        try:
            return DatasetType(str(dataset).lower())
        except ValueError:
            for d_type in DatasetType:
                if d_type.value == str(dataset).lower():
                    return d_type
            raise ETLValidationError(
                message=f"Unsupported or unregistered dataset identifier: '{dataset}'",
                details=f"Allowed values: {[d.value for d in DatasetType]}",
            )

    # -------------------------------------------------------------------------
    # Generic Schema Validation Checks
    # -------------------------------------------------------------------------

    def _check_required_columns(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> ValidationCheck:
        missing = [col for col in schema.required_columns if col not in df.columns]
        if missing:
            return ValidationCheck(
                check_name="required_columns",
                status=ValidationResult.FAILED,
                severity=ValidationSeverity.CRITICAL,
                message=f"Missing required columns: {missing}",
                details={"missing": missing, "expected": schema.required_columns},
            )
        return ValidationCheck(
            check_name="required_columns",
            status=ValidationResult.PASSED,
            severity=ValidationSeverity.INFO,
            message="All required columns are present.",
        )

    def _check_unexpected_columns(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> ValidationCheck:
        allowed = set(schema.required_columns) | set(schema.optional_columns)
        unexpected = [col for col in df.columns if col not in allowed]
        if unexpected:
            return ValidationCheck(
                check_name="unexpected_columns",
                status=ValidationResult.WARNING,
                severity=ValidationSeverity.WARNING,
                message=f"Found unexpected columns: {unexpected}",
                details={"unexpected": unexpected},
            )
        return ValidationCheck(
            check_name="unexpected_columns",
            status=ValidationResult.PASSED,
            severity=ValidationSeverity.INFO,
            message="No unexpected columns detected.",
        )

    def _check_primary_key_uniqueness(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[ValidationCheck, List[int]]:
        invalid_indices: List[int] = []
        if not schema.primary_key or schema.primary_key not in df.columns:
            return (
                ValidationCheck(
                    check_name="primary_key_uniqueness",
                    status=ValidationResult.PASSED,
                    severity=ValidationSeverity.INFO,
                    message="No primary key defined or column not present.",
                ),
                invalid_indices,
            )

        pk_col = schema.primary_key
        duplicates_mask = df.duplicated(subset=[pk_col], keep=False)
        dup_count = int(duplicates_mask.sum())
        null_count = int(df[pk_col].isnull().sum())

        if dup_count > 0 or null_count > 0:
            invalid_indices = df[duplicates_mask | df[pk_col].isnull()].index.tolist()
            severity = ValidationSeverity.CRITICAL if null_count > 0 else ValidationSeverity.ERROR
            return (
                ValidationCheck(
                    check_name="primary_key_uniqueness",
                    status=ValidationResult.FAILED,
                    severity=severity,
                    message=f"Primary key '{pk_col}' has {dup_count} duplicate values and {null_count} nulls.",
                    details={"duplicates": dup_count, "nulls": null_count},
                ),
                invalid_indices,
            )

        return (
            ValidationCheck(
                check_name="primary_key_uniqueness",
                status=ValidationResult.PASSED,
                severity=ValidationSeverity.INFO,
                message=f"Primary key '{pk_col}' is unique and non-null.",
            ),
            [],
        )

    def _check_composite_key_uniqueness(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[ValidationCheck, List[int]]:
        invalid_indices: List[int] = []
        if not schema.composite_keys or not all(
            k in df.columns for k in schema.composite_keys
        ):
            return (
                ValidationCheck(
                    check_name="composite_key_uniqueness",
                    status=ValidationResult.PASSED,
                    severity=ValidationSeverity.INFO,
                    message="No composite keys defined or columns missing.",
                ),
                invalid_indices,
            )

        keys = schema.composite_keys
        duplicates_mask = df.duplicated(subset=keys, keep=False)
        dup_count = int(duplicates_mask.sum())

        if dup_count > 0:
            invalid_indices = df[duplicates_mask].index.tolist()
            return (
                ValidationCheck(
                    check_name="composite_key_uniqueness",
                    status=ValidationResult.FAILED,
                    severity=ValidationSeverity.ERROR,
                    message=f"Composite key {keys} has {dup_count} duplicate rows.",
                    details={"duplicates": dup_count, "keys": keys},
                ),
                invalid_indices,
            )

        return (
            ValidationCheck(
                check_name="composite_key_uniqueness",
                status=ValidationResult.PASSED,
                severity=ValidationSeverity.INFO,
                message=f"Composite key {keys} is unique across all rows.",
            ),
            [],
        )

    def _check_nullable_fields(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[ValidationCheck, List[int]]:
        invalid_indices: List[int] = []
        non_nullable = [
            col
            for col in schema.required_columns
            if col in df.columns and col not in schema.nullable_columns
        ]

        violating_cols: Dict[str, int] = {}
        for col in non_nullable:
            null_count = int(df[col].isnull().sum())
            if null_count > 0:
                violating_cols[col] = null_count
                invalid_indices.extend(df[df[col].isnull()].index.tolist())

        if violating_cols:
            invalid_indices = list(set(invalid_indices))
            return (
                ValidationCheck(
                    check_name="nullable_fields",
                    status=ValidationResult.FAILED,
                    severity=ValidationSeverity.ERROR,
                    message=f"Non-nullable columns contain null values: {violating_cols}",
                    details={"violations": violating_cols},
                ),
                invalid_indices,
            )

        return (
            ValidationCheck(
                check_name="nullable_fields",
                status=ValidationResult.PASSED,
                severity=ValidationSeverity.INFO,
                message="Non-nullable columns contain zero null values.",
            ),
            [],
        )

    def _check_enum_fields(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[ValidationCheck, List[int]]:
        invalid_indices: List[int] = []
        enum_violations: Dict[str, int] = {}

        for col, allowed_values in schema.enum_fields.items():
            if col in df.columns:
                non_null_series = df[col].dropna()
                invalid_mask = ~non_null_series.isin(allowed_values)
                invalid_cnt = int(invalid_mask.sum())
                if invalid_cnt > 0:
                    enum_violations[col] = invalid_cnt
                    invalid_indices.extend(
                        non_null_series[invalid_mask].index.tolist()
                    )

        if enum_violations:
            invalid_indices = list(set(invalid_indices))
            return (
                ValidationCheck(
                    check_name="enum_fields",
                    status=ValidationResult.FAILED,
                    severity=ValidationSeverity.ERROR,
                    message=f"Enum column value violations detected: {enum_violations}",
                    details={"violations": enum_violations},
                ),
                invalid_indices,
            )

        return (
            ValidationCheck(
                check_name="enum_fields",
                status=ValidationResult.PASSED,
                severity=ValidationSeverity.INFO,
                message="All enum columns contain valid values.",
            ),
            [],
        )

    def _check_numeric_constraints(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[ValidationCheck, List[int]]:
        invalid_indices: List[int] = []
        violations: Dict[str, int] = {}

        for col, constraint in schema.numeric_constraints.items():
            if col in df.columns:
                series = pd.to_numeric(df[col], errors="coerce").dropna()
                invalid_mask = pd.Series(False, index=series.index)

                if constraint.min_value is not None:
                    invalid_mask |= series < constraint.min_value
                if constraint.max_value is not None:
                    invalid_mask |= series > constraint.max_value
                if not constraint.allow_zero:
                    invalid_mask |= series == 0.0

                cnt = int(invalid_mask.sum())
                if cnt > 0:
                    violations[col] = cnt
                    invalid_indices.extend(series[invalid_mask].index.tolist())

        if violations:
            invalid_indices = list(set(invalid_indices))
            return (
                ValidationCheck(
                    check_name="numeric_constraints",
                    status=ValidationResult.FAILED,
                    severity=ValidationSeverity.ERROR,
                    message=f"Numeric boundary violations detected: {violations}",
                    details={"violations": violations},
                ),
                invalid_indices,
            )

        return (
            ValidationCheck(
                check_name="numeric_constraints",
                status=ValidationResult.PASSED,
                severity=ValidationSeverity.INFO,
                message="All numeric constraints are respected.",
            ),
            [],
        )

    def _check_date_fields(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[ValidationCheck, List[int]]:
        invalid_indices: List[int] = []
        date_violations: Dict[str, int] = {}

        for col in schema.date_fields:
            if col in df.columns:
                non_null_series = df[col].dropna()
                parsed = pd.to_datetime(non_null_series, errors="coerce")
                invalid_cnt = int(parsed.isnull().sum())
                if invalid_cnt > 0:
                    date_violations[col] = invalid_cnt
                    invalid_indices.extend(
                        non_null_series[parsed.isnull()].index.tolist()
                    )

        if date_violations:
            invalid_indices = list(set(invalid_indices))
            return (
                ValidationCheck(
                    check_name="date_fields",
                    status=ValidationResult.FAILED,
                    severity=ValidationSeverity.ERROR,
                    message=f"Date parsing errors detected: {date_violations}",
                    details={"violations": date_violations},
                ),
                invalid_indices,
            )

        return (
            ValidationCheck(
                check_name="date_fields",
                status=ValidationResult.PASSED,
                severity=ValidationSeverity.INFO,
                message="All date fields are valid timestamps.",
            ),
            [],
        )

    def _check_pandas_dtypes(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> ValidationCheck:
        dtype_mismatches: Dict[str, Dict[str, str]] = {}
        for col, expected_dtype in schema.expected_dtypes.items():
            if col in df.columns:
                actual_dtype = str(df[col].dtype)
                if actual_dtype != expected_dtype:
                    dtype_mismatches[col] = {
                        "expected": expected_dtype,
                        "actual": actual_dtype,
                    }

        if dtype_mismatches:
            return ValidationCheck(
                check_name="pandas_dtypes",
                status=ValidationResult.WARNING,
                severity=ValidationSeverity.INFO,
                message=f"Dtype mismatches detected (will be cast during ETL): {dtype_mismatches}",
                details={"mismatches": dtype_mismatches},
            )

        return ValidationCheck(
            check_name="pandas_dtypes",
            status=ValidationResult.PASSED,
            severity=ValidationSeverity.INFO,
            message="All pandas column dtypes match expected schema types.",
        )

    # -------------------------------------------------------------------------
    # Dataset-Specific Validations
    # -------------------------------------------------------------------------

    def _check_customers_specific(self, df: pd.DataFrame) -> Tuple[List[ValidationCheck], List[int]]:
        checks: List[ValidationCheck] = []
        invalid_indices: List[int] = []

        if "customer_state" in df.columns:
            allowed_states = {
                "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
                "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
                "RO", "RR", "RS", "SC", "SE", "SP", "TO"
            }
            invalid_states = df[~df["customer_state"].isin(allowed_states)]
            if len(invalid_states) > 0:
                checks.append(
                    ValidationCheck(
                        check_name="customers_brazilian_state_code",
                        status=ValidationResult.FAILED,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_states)} customer records with invalid Brazilian state codes.",
                    )
                )
                invalid_indices.extend(invalid_states.index.tolist())
            else:
                checks.append(
                    ValidationCheck(
                        check_name="customers_brazilian_state_code",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All customer state codes are valid Brazilian state abbreviations.",
                    )
                )

        if "customer_zip_code_prefix" in df.columns:
            zips = pd.to_numeric(df["customer_zip_code_prefix"], errors="coerce")
            invalid_zips = df[zips.isnull() | (zips < 0) | (zips > 99999)]
            if len(invalid_zips) > 0:
                checks.append(
                    ValidationCheck(
                        check_name="customers_zip_prefix_bounds",
                        status=ValidationResult.FAILED,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_zips)} invalid customer zip code prefixes.",
                    )
                )
                invalid_indices.extend(invalid_zips.index.tolist())
            else:
                checks.append(
                    ValidationCheck(
                        check_name="customers_zip_prefix_bounds",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All customer zip code prefixes are within valid 5-digit numerical bounds.",
                    )
                )

        return checks, invalid_indices

    def _check_orders_specific(
        self,
        df: pd.DataFrame,
        parent_dfs: Optional[Dict[DatasetType, pd.DataFrame]] = None,
    ) -> Tuple[List[ValidationCheck], List[int]]:
        checks: List[ValidationCheck] = []
        invalid_indices: List[int] = []

        if "order_status" in df.columns:
            valid_statuses = {"created", "approved", "processing", "invoiced", "shipped", "delivered", "unavailable", "canceled"}
            invalid_status = df[~df["order_status"].isin(valid_statuses)]
            if len(invalid_status) > 0:
                checks.append(
                    ValidationCheck(
                        check_name="orders_status_enum",
                        status=ValidationResult.FAILED,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_status)} orders with invalid order_status.",
                    )
                )
                invalid_indices.extend(invalid_status.index.tolist())
            else:
                checks.append(
                    ValidationCheck(
                        check_name="orders_status_enum",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All order_status values match expected lifecycle enums.",
                    )
                )

        date_cols = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date", "order_delivered_customer_date"]
        if all(c in df.columns for c in date_cols):
            p_date = pd.to_datetime(df["order_purchase_timestamp"], errors="coerce")
            a_date = pd.to_datetime(df["order_approved_at"], errors="coerce")
            c_date = pd.to_datetime(df["order_delivered_carrier_date"], errors="coerce")
            d_date = pd.to_datetime(df["order_delivered_customer_date"], errors="coerce")

            invalid_appr = df[a_date.notnull() & (p_date > a_date)]
            invalid_carr = df[a_date.notnull() & c_date.notnull() & (a_date > c_date)]
            invalid_cust = df[c_date.notnull() & d_date.notnull() & (c_date > d_date)]

            total_ts_violations = len(invalid_appr) + len(invalid_carr) + len(invalid_cust)
            if total_ts_violations > 0:
                checks.append(
                    ValidationCheck(
                        check_name="orders_timestamp_sequence",
                        status=ValidationResult.WARNING,
                        severity=ValidationSeverity.WARNING,
                        message=f"Detected {total_ts_violations} order records with out-of-sequence timestamps.",
                    )
                )
                invalid_indices.extend(invalid_appr.index.tolist() + invalid_carr.index.tolist() + invalid_cust.index.tolist())
            else:
                checks.append(
                    ValidationCheck(
                        check_name="orders_timestamp_sequence",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All order milestone timestamps follow chronological sequence.",
                    )
                )

        if parent_dfs and DatasetType.CUSTOMERS in parent_dfs and "customer_id" in df.columns:
            cust_df = parent_dfs[DatasetType.CUSTOMERS]
            valid_cust_ids = set(cust_df["customer_id"].dropna())
            orphaned = df[~df["customer_id"].isin(valid_cust_ids)]
            if len(orphaned) > 0:
                checks.append(
                    ValidationCheck(
                        check_name="orders_customer_foreign_key",
                        status=ValidationResult.FAILED,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(orphaned)} orders referencing non-existent customer_id values.",
                    )
                )
                invalid_indices.extend(orphaned.index.tolist())
            else:
                checks.append(
                    ValidationCheck(
                        check_name="orders_customer_foreign_key",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All order customer_id values exist in customers parent dataset.",
                    )
                )

        return checks, invalid_indices

    def _check_products_specific(
        self,
        df: pd.DataFrame,
        parent_dfs: Optional[Dict[DatasetType, pd.DataFrame]] = None,
    ) -> Tuple[List[ValidationCheck], List[int]]:
        checks: List[ValidationCheck] = []
        invalid_indices: List[int] = []

        dim_cols = ["product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"]
        violating_dims = pd.Series(False, index=df.index)
        for col in dim_cols:
            if col in df.columns:
                vals = pd.to_numeric(df[col], errors="coerce")
                violating_dims |= (vals.notnull() & (vals < 0))

        if violating_dims.sum() > 0:
            checks.append(
                ValidationCheck(
                    check_name="products_dimensions_non_negative",
                    status=ValidationResult.FAILED,
                    severity=ValidationSeverity.ERROR,
                    message=f"Found {violating_dims.sum()} product records with negative physical dimensions/weight.",
                )
            )
            invalid_indices.extend(df[violating_dims].index.tolist())
        else:
            checks.append(
                ValidationCheck(
                    check_name="products_dimensions_non_negative",
                    status=ValidationResult.PASSED,
                    severity=ValidationSeverity.INFO,
                    message="All product weights and physical dimensions are >= 0.",
                )
            )

        if parent_dfs and DatasetType.TRANSLATIONS in parent_dfs and "product_category_name" in df.columns:
            trans_df = parent_dfs[DatasetType.TRANSLATIONS]
            valid_cats = set(trans_df["product_category_name"].dropna())
            unmapped = df[df["product_category_name"].notnull() & ~df["product_category_name"].isin(valid_cats)]
            if len(unmapped) > 0:
                checks.append(
                    ValidationCheck(
                        check_name="products_translation_existence",
                        status=ValidationResult.WARNING,
                        severity=ValidationSeverity.WARNING,
                        message=f"Found {len(unmapped)} product categories missing from English translation table.",
                    )
                )
            else:
                checks.append(
                    ValidationCheck(
                        check_name="products_translation_existence",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All product categories exist in category translation table.",
                    )
                )

        return checks, invalid_indices

    def _check_payments_specific(self, df: pd.DataFrame) -> Tuple[List[ValidationCheck], List[int]]:
        checks: List[ValidationCheck] = []
        invalid_indices: List[int] = []

        if "payment_value" in df.columns:
            vals = pd.to_numeric(df["payment_value"], errors="coerce")
            invalid_val = df[vals.isnull() | (vals < 0)]
            if len(invalid_val) > 0:
                checks.append(
                    ValidationCheck(
                        check_name="payments_value_non_negative",
                        status=ValidationResult.FAILED,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_val)} payment records with negative payment_value.",
                    )
                )
                invalid_indices.extend(invalid_val.index.tolist())
            else:
                checks.append(
                    ValidationCheck(
                        check_name="payments_value_non_negative",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All payment_value amounts are >= 0.0.",
                    )
                )

        if "payment_installments" in df.columns:
            inst = pd.to_numeric(df["payment_installments"], errors="coerce")
            invalid_inst = df[inst.isnull() | (inst < 0)]
            if len(invalid_inst) > 0:
                checks.append(
                    ValidationCheck(
                        check_name="payments_installments_non_negative",
                        status=ValidationResult.FAILED,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_inst)} payment records with negative installments.",
                    )
                )
                invalid_indices.extend(invalid_inst.index.tolist())
            else:
                checks.append(
                    ValidationCheck(
                        check_name="payments_installments_non_negative",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All payment installment terms are >= 0.",
                    )
                )

        return checks, invalid_indices

    def _check_reviews_specific(self, df: pd.DataFrame) -> Tuple[List[ValidationCheck], List[int]]:
        checks: List[ValidationCheck] = []
        invalid_indices: List[int] = []

        if "review_score" in df.columns:
            scores = pd.to_numeric(df["review_score"], errors="coerce")
            invalid_scores = df[scores.isnull() | (scores < 1) | (scores > 5)]
            if len(invalid_scores) > 0:
                checks.append(
                    ValidationCheck(
                        check_name="reviews_score_range_1_to_5",
                        status=ValidationResult.FAILED,
                        severity=ValidationSeverity.ERROR,
                        message=f"Found {len(invalid_scores)} review records with score outside 1–5 range.",
                    )
                )
                invalid_indices.extend(invalid_scores.index.tolist())
            else:
                checks.append(
                    ValidationCheck(
                        check_name="reviews_score_range_1_to_5",
                        status=ValidationResult.PASSED,
                        severity=ValidationSeverity.INFO,
                        message="All review_score ratings are within valid 1–5 star range.",
                    )
                )

        return checks, invalid_indices

    # -------------------------------------------------------------------------
    # Public Validation Methods
    # -------------------------------------------------------------------------

    def validate_dataset(
        self,
        dataset: Union[DatasetType, str],
        df: pd.DataFrame,
        parent_dfs: Optional[Dict[Union[DatasetType, str], pd.DataFrame]] = None,
    ) -> ValidationReport:
        """
        Validate a single dataset DataFrame against its schema and domain rules.

        Args:
            dataset: DatasetType enum or dataset name string.
            df: Input dataset pandas DataFrame.
            parent_dfs: Optional dictionary of parent DataFrames for FK checks.

        Returns:
            ValidationReport detailing passed/failed checks and statistics.
        """
        start_time = time.perf_counter()
        d_type = self._resolve_dataset_type(dataset)
        logger.info(f"Initiating validation for dataset: '{d_type.value}' ({len(df):,} rows)")

        schema = self.registry.get(d_type.value)

        resolved_parents: Dict[DatasetType, pd.DataFrame] = {}
        if parent_dfs:
            for k, v in parent_dfs.items():
                resolved_parents[self._resolve_dataset_type(k)] = v

        all_checks: List[ValidationCheck] = []
        invalid_indices_set: Set[int] = set()

        # Run Generic Schema Checks
        chk_req = self._check_required_columns(df, schema)
        all_checks.append(chk_req)

        chk_unexp = self._check_unexpected_columns(df, schema)
        all_checks.append(chk_unexp)

        chk_pk, idx_pk = self._check_primary_key_uniqueness(df, schema)
        all_checks.append(chk_pk)
        invalid_indices_set.update(idx_pk)

        chk_comp, idx_comp = self._check_composite_key_uniqueness(df, schema)
        all_checks.append(chk_comp)
        invalid_indices_set.update(idx_comp)

        chk_null, idx_null = self._check_nullable_fields(df, schema)
        all_checks.append(chk_null)
        invalid_indices_set.update(idx_null)

        chk_enum, idx_enum = self._check_enum_fields(df, schema)
        all_checks.append(chk_enum)
        invalid_indices_set.update(idx_enum)

        chk_num, idx_num = self._check_numeric_constraints(df, schema)
        all_checks.append(chk_num)
        invalid_indices_set.update(idx_num)

        chk_dt, idx_dt = self._check_date_fields(df, schema)
        all_checks.append(chk_dt)
        invalid_indices_set.update(idx_dt)

        chk_dtype = self._check_pandas_dtypes(df, schema)
        all_checks.append(chk_dtype)

        # Run Dataset-Specific Checks
        spec_checks: List[ValidationCheck] = []
        spec_idx: List[int] = []

        if d_type == DatasetType.CUSTOMERS:
            spec_checks, spec_idx = self._check_customers_specific(df)
        elif d_type == DatasetType.ORDERS:
            spec_checks, spec_idx = self._check_orders_specific(df, resolved_parents)
        elif d_type == DatasetType.PRODUCTS:
            spec_checks, spec_idx = self._check_products_specific(df, resolved_parents)
        elif d_type == DatasetType.PAYMENTS:
            spec_checks, spec_idx = self._check_payments_specific(df)
        elif d_type == DatasetType.REVIEWS:
            spec_checks, spec_idx = self._check_reviews_specific(df)

        all_checks.extend(spec_checks)
        invalid_indices_set.update(spec_idx)

        # Summarize Results
        passed: List[str] = []
        failed: List[str] = []
        warnings: List[str] = []

        for chk in all_checks:
            if chk.status == ValidationResult.PASSED:
                passed.append(chk.check_name)
            elif chk.status == ValidationResult.FAILED:
                failed.append(f"[{chk.severity.value}] {chk.check_name}: {chk.message}")
            elif chk.status == ValidationResult.WARNING:
                warnings.append(f"[{chk.severity.value}] {chk.check_name}: {chk.message}")

        overall_status = ValidationResult.PASSED
        if any(c.status == ValidationResult.FAILED for c in all_checks):
            overall_status = ValidationResult.FAILED
        elif any(c.status == ValidationResult.WARNING for c in all_checks):
            overall_status = ValidationResult.WARNING

        elapsed_sec = time.perf_counter() - start_time
        invalid_indices_list = sorted(list(invalid_indices_set))

        report = ValidationReport(
            dataset=d_type,
            total_rows=len(df),
            status=overall_status,
            passed_checks=passed,
            failed_checks=failed,
            warnings=warnings,
            checks=all_checks,
            execution_time_sec=round(elapsed_sec, 4),
            statistics={
                "total_checks": len(all_checks),
                "passed_count": len(passed),
                "failed_count": len(failed),
                "warning_count": len(warnings),
                "invalid_row_count": len(invalid_indices_list),
            },
            invalid_row_indices=invalid_indices_list,
        )

        logger.info(
            f"Completed validation for '{d_type.value}' in {elapsed_sec:.4f}s | "
            f"Status: {overall_status.value} | Critical: {report.critical_count} | Error: {report.error_count} | Warning: {report.warning_count}"
        )
        return report

    def validate_batch(
        self, datasets: Dict[Union[DatasetType, str], pd.DataFrame]
    ) -> ValidationSummary:
        """
        Validate an entire batch of dataset DataFrames in dependency order.

        Args:
            datasets: Dictionary mapping DatasetType or dataset names to DataFrames.

        Returns:
            ValidationSummary aggregating reports across all datasets.
        """
        start_time = time.perf_counter()
        logger.info(f"Initiating batch validation across {len(datasets)} datasets...")

        resolved_batch: Dict[DatasetType, pd.DataFrame] = {}
        for k, df in datasets.items():
            resolved_batch[self._resolve_dataset_type(k)] = df

        reports: Dict[DatasetType, ValidationReport] = {}
        failed_count = 0
        passed_count = 0

        eval_order = [
            DatasetType.TRANSLATIONS,
            DatasetType.CUSTOMERS,
            DatasetType.PRODUCTS,
            DatasetType.ORDERS,
            DatasetType.ORDER_ITEMS,
            DatasetType.PAYMENTS,
            DatasetType.REVIEWS,
        ]

        for d_type in eval_order:
            if d_type in resolved_batch:
                df = resolved_batch[d_type]
                report = self.validate_dataset(d_type, df, parent_dfs=resolved_batch)
                reports[d_type] = report
                if report.status == ValidationResult.FAILED:
                    failed_count += 1
                else:
                    passed_count += 1

        overall_status = ValidationResult.PASSED
        if failed_count > 0:
            overall_status = ValidationResult.FAILED
        elif any(r.status == ValidationResult.WARNING for r in reports.values()):
            overall_status = ValidationResult.WARNING

        total_elapsed = time.perf_counter() - start_time
        summary = ValidationSummary(
            reports=reports,
            total_datasets=len(reports),
            passed_datasets=passed_count,
            failed_datasets=failed_count,
            overall_status=overall_status,
            total_execution_time_sec=round(total_elapsed, 4),
        )

        logger.info(
            f"Completed batch validation in {total_elapsed:.4f}s | "
            f"Overall Status: {overall_status.value} | Can Continue: {summary.can_continue()}"
        )

        # Trigger Circuit Breaker if pipeline cannot continue due to CRITICAL failures
        if not summary.can_continue():
            critical_datasets = [
                d.value for d, r in reports.items() if r.has_critical()
            ]
            error_msg = f"ETL Pipeline halted due to CRITICAL validation failures on datasets: {critical_datasets}"
            logger.error(error_msg)
            raise CircuitBreakerTriggeredError(
                message=error_msg,
                details=f"Critical datasets: {critical_datasets}",
            )

        return summary
