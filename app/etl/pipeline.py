"""
ETL Pipeline Orchestrator for Customer Intelligence Platform.

Coordinates Extract, Validate, Transform, and Load stages sequentially with stage logging,
circuit breaker enforcement, checkpoint/resume management, and comprehensive pipeline reporting.
"""

from dataclasses import dataclass, field
import time
from typing import Any, Dict, List, Optional, Set, Union
from loguru import logger
import pandas as pd
from sqlalchemy.orm import Session

from app.etl.checkpoint import CheckpointManager, PipelineCheckpointState
from app.etl.config import ETLSettings, etl_settings
from app.etl.extract.csv_loader import CSVLoader
from app.etl.load.postgres_loader import PostgresLoader
from app.etl.load.report import LoadReport, LoadSummary
from app.etl.schemas.schema_registry import SchemaRegistry, schema_registry
from app.etl.transform.report import TransformationReport, TransformationSummary
from app.etl.transform.transformers import DataTransformer
from app.etl.utils.dataset_types import DatasetType
from app.etl.utils.exceptions import CircuitBreakerTriggeredError, ETLException
from app.etl.validate.report import (
    ValidationReport,
    ValidationResult,
    ValidationSummary,
)
from app.etl.validate.validators import Validator


@dataclass
class PipelineReport:
    """
    End-to-end execution summary report for the ETL Pipeline.
    """

    extraction_summary: Dict[DatasetType, Dict[str, Any]] = field(default_factory=dict)
    validation_summary: ValidationSummary = field(default_factory=ValidationSummary)
    transformation_summary: TransformationSummary = field(
        default_factory=TransformationSummary
    )
    load_summary: Optional[LoadSummary] = None
    total_execution_time_sec: float = 0.0
    overall_status: str = "SUCCESS"  # SUCCESS, WARNING, FAILED
    execution_order: List[DatasetType] = field(default_factory=list)

    @property
    def is_successful(self) -> bool:
        """
        Check if end-to-end pipeline execution succeeded cleanly.
        """
        return self.overall_status in ("SUCCESS", "WARNING")


class ETLPipeline:
    """
    Sequential ETL Pipeline Orchestrator executing Extract, Validate, Transform, and Load stages.
    """

    def __init__(
        self,
        batch_size: Optional[int] = None,
        stop_on_error: bool = True,
        verbose_logging: bool = True,
        resume: bool = False,
        checkpoint: bool = True,
        checkpoint_manager: Optional[CheckpointManager] = None,
        loader: Optional[CSVLoader] = None,
        validator: Optional[Validator] = None,
        transformer: Optional[DataTransformer] = None,
        postgres_loader: Optional[PostgresLoader] = None,
        settings: Optional[ETLSettings] = None,
    ) -> None:
        """
        Initialize ETLPipeline with stage configurations, dependencies, and checkpoint options.

        Args:
            batch_size: Database bulk insert chunk size.
            stop_on_error: Whether to halt pipeline on critical validation/load errors.
            verbose_logging: Enable detailed loguru output.
            resume: Whether to detect and resume from existing pipeline checkpoint.
            checkpoint: Whether to create/update progress checkpoints after each dataset.
            checkpoint_manager: Custom CheckpointManager instance.
            loader: Extraction component instance.
            validator: Validation component instance.
            transformer: Transformation component instance.
            postgres_loader: Database loading component instance.
            settings: Application ETL Settings instance.
        """
        self.settings = settings or etl_settings
        self.batch_size = batch_size or self.settings.BATCH_SIZE
        self.stop_on_error = stop_on_error
        self.verbose_logging = verbose_logging
        self.resume = resume
        self.checkpoint = checkpoint
        self.checkpoint_manager = checkpoint_manager or CheckpointManager()

        self.loader = loader or CSVLoader(settings=self.settings)
        self.validator = validator or Validator(settings=self.settings)
        self.transformer = transformer or DataTransformer(settings=self.settings)
        self.postgres_loader = postgres_loader or PostgresLoader(
            batch_size=self.batch_size, settings=self.settings
        )

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
            raise ETLException(
                message=f"Unsupported or unregistered dataset identifier: '{dataset}'"
            )

    def run_dataset(
        self,
        dataset: Union[DatasetType, str],
        session: Optional[Session] = None,
        context_dfs: Optional[Dict[DatasetType, pd.DataFrame]] = None,
    ) -> PipelineReport:
        """
        Execute end-to-end ETL stages sequentially for a single dataset.

        Args:
            dataset: DatasetType enum or dataset name string.
            session: Optional SQLAlchemy Session for database loading.
            context_dfs: Optional dictionary of context DataFrames for validations/transforms.

        Returns:
            PipelineReport summarizing all stage results.

        Raises:
            CircuitBreakerTriggeredError: If validation produces CRITICAL failures.
        """
        pipeline_start = time.perf_counter()
        d_type = self._resolve_dataset_type(dataset)
        logger.info(f"=== Starting ETL Pipeline execution for dataset: '{d_type.value}' ===")

        # Stage 1: Extract
        logger.info(f"[STAGE 1/4: EXTRACT] Extracting raw CSV for dataset '{d_type.value}'...")
        ext_start = time.perf_counter()
        raw_df = self.loader.load_dataset(d_type.value)
        ext_time = time.perf_counter() - ext_start
        logger.info(f"[STAGE 1/4: EXTRACT] Completed extraction for '{d_type.value}' ({len(raw_df):,} rows) in {ext_time:.4f}s.")

        extraction_summary = {
            d_type: {
                "rows_extracted": len(raw_df),
                "columns": list(raw_df.columns),
                "execution_time_sec": round(ext_time, 4),
            }
        }

        # Stage 2: Validate
        logger.info(f"[STAGE 2/4: VALIDATE] Validating schema & domain rules for '{d_type.value}'...")
        val_report = self.validator.validate_dataset(d_type, raw_df, parent_dfs=context_dfs)
        val_summary = ValidationSummary(
            reports={d_type: val_report},
            total_datasets=1,
            passed_datasets=1 if val_report.is_valid else 0,
            failed_datasets=0 if val_report.is_valid else 1,
            overall_status=val_report.status,
            total_execution_time_sec=val_report.execution_time_sec,
        )
        logger.info(f"[STAGE 2/4: VALIDATE] Completed validation for '{d_type.value}'. Status: {val_report.status.value}")

        # Circuit Breaker Check
        if not val_report.can_continue():
            error_msg = f"Circuit Breaker Triggered: Dataset '{d_type.value}' produced CRITICAL validation errors."
            logger.error(error_msg)
            if self.checkpoint:
                self.checkpoint_manager.save_checkpoint(
                    completed_datasets=[],
                    current_dataset=d_type,
                    stage="VALIDATE",
                    status="FAILED",
                )
            raise CircuitBreakerTriggeredError(
                message=error_msg,
                details=f"Critical errors: {val_report.failed_checks}",
            )

        # Stage 3: Transform
        logger.info(f"[STAGE 3/4: TRANSFORM] Executing cleansing & operational derivations for '{d_type.value}'...")
        trans_df, trans_report = self.transformer.transform_dataset(d_type, raw_df, context_dfs=context_dfs)
        trans_summary = TransformationSummary(
            reports={d_type: trans_report},
            total_datasets=1,
            total_execution_time_sec=trans_report.execution_time_sec,
        )
        logger.info(f"[STAGE 3/4: TRANSFORM] Completed transformation for '{d_type.value}' ({len(trans_df):,} rows) in {trans_report.execution_time_sec:.4f}s.")

        # Stage 4: Load (Optional if session is provided)
        load_summary: Optional[LoadSummary] = None
        if session:
            logger.info(f"[STAGE 4/4: LOAD] Loading dataset '{d_type.value}' into PostgreSQL database...")
            load_report = self.postgres_loader.load_dataset(d_type, trans_df, session=session)
            load_summary = LoadSummary(
                reports={d_type: load_report},
                total_datasets=1,
                total_attempted=load_report.rows_attempted,
                total_inserted=load_report.rows_inserted,
                total_skipped=load_report.rows_skipped,
                total_execution_time_sec=load_report.execution_time_sec,
            )
            logger.info(f"[STAGE 4/4: LOAD] Completed database load for '{d_type.value}' ({load_report.rows_inserted:,} rows inserted).")
        else:
            logger.info(f"[STAGE 4/4: LOAD] Database session omitted. Skipping PostgreSQL database insertion.")

        total_elapsed = time.perf_counter() - pipeline_start

        overall_status = "SUCCESS"
        if val_report.status == ValidationResult.FAILED or (load_summary and any(r.rows_inserted < r.rows_attempted for r in load_summary.reports.values())):
            overall_status = "FAILED"
        elif val_report.status == ValidationResult.WARNING:
            overall_status = "WARNING"

        # Record checkpoint progress if enabled
        if self.checkpoint and overall_status in ("SUCCESS", "WARNING"):
            self.checkpoint_manager.save_checkpoint(
                completed_datasets=[d_type],
                current_dataset=d_type,
                stage="LOAD",
                status="SUCCESS",
            )

        logger.info(f"=== ETL Pipeline completed for '{d_type.value}' in {total_elapsed:.4f}s | Status: {overall_status} ===")

        return PipelineReport(
            extraction_summary=extraction_summary,
            validation_summary=val_summary,
            transformation_summary=trans_summary,
            load_summary=load_summary,
            total_execution_time_sec=round(total_elapsed, 4),
            overall_status=overall_status,
            execution_order=[d_type],
        )

    def run_all(self, session: Optional[Session] = None) -> PipelineReport:
        """
        Execute end-to-end ETL pipeline for all datasets in topological dependency order.

        Args:
            session: Optional SQLAlchemy Session for database loading.

        Returns:
            PipelineReport summarizing batch execution across all 5 stages.

        Raises:
            CircuitBreakerTriggeredError: If batch validation produces CRITICAL failures.
        """
        pipeline_start = time.perf_counter()
        logger.info("=================================================================")
        logger.info("   STARTING END-TO-END ETL PIPELINE BATCH EXECUTION")
        logger.info("=================================================================")

        # Detect and restore checkpoint state if resume is enabled
        completed_datasets_set: Set[str] = set()
        if self.resume:
            checkpoint_state = self.checkpoint_manager.load_checkpoint()
            if checkpoint_state and checkpoint_state.completed_datasets:
                completed_datasets_set = set(checkpoint_state.completed_datasets)
                logger.info(
                    f"[RESUME ENGINE] Resuming execution. Skipping {len(completed_datasets_set)} already completed datasets: {list(completed_datasets_set)}"
                )

        # Stage 1: Extract All Raw Datasets
        logger.info("[STAGE 1/5: EXTRACT] Extracting raw CSV datasets from data/raw/...")
        ext_start = time.perf_counter()
        raw_datasets = self.loader.load_all_raw_datasets()
        ext_time = time.perf_counter() - ext_start

        extraction_summary: Dict[DatasetType, Dict[str, Any]] = {}
        for filename, df in raw_datasets.items():
            d_type = self.loader.detect_dataset_type(filename)
            if d_type:
                extraction_summary[d_type] = {
                    "filename": filename,
                    "rows_extracted": len(df),
                    "columns_count": len(df.columns),
                }

        logger.info(f"[STAGE 1/5: EXTRACT] Completed extraction across {len(raw_datasets)} CSV files in {ext_time:.4f}s.")

        raw_batch: Dict[DatasetType, pd.DataFrame] = {}
        for filename, df in raw_datasets.items():
            d_type = self.loader.detect_dataset_type(filename)
            if d_type:
                raw_batch[d_type] = df

        # Filter out datasets already completed if resuming
        active_raw_batch = {
            k: v for k, v in raw_batch.items() if k.value not in completed_datasets_set
        }
        if len(active_raw_batch) < len(raw_batch):
            logger.info(
                f"[RESUME ENGINE] Filtered active batch to {len(active_raw_batch)} remaining datasets: {[d.value for d in active_raw_batch.keys()]}"
            )

        # Stage 2: Validate Batch
        logger.info("[STAGE 2/5: VALIDATE] Executing batch validation across active datasets...")
        val_summary = self.validator.validate_batch(raw_batch)
        logger.info(f"[STAGE 2/5: VALIDATE] Completed batch validation. Overall Status: {val_summary.overall_status.value}")

        # Circuit Breaker Check on Batch Validation
        if not val_summary.can_continue():
            critical_datasets = [
                d.value for d, r in val_summary.reports.items() if r.has_critical()
            ]
            error_msg = f"Circuit Breaker Triggered: Pipeline halted due to CRITICAL validation failures on: {critical_datasets}"
            logger.error(error_msg)
            if self.checkpoint:
                self.checkpoint_manager.save_checkpoint(
                    completed_datasets=list(completed_datasets_set),
                    current_dataset=critical_datasets[0] if critical_datasets else None,
                    stage="VALIDATE",
                    status="FAILED",
                )
            raise CircuitBreakerTriggeredError(
                message=error_msg,
                details=f"Critical failure datasets: {critical_datasets}",
            )

        # Stage 3: Transform Batch
        logger.info("[STAGE 3/5: TRANSFORM] Executing batch transformations & operational derivations...")
        transformed_batch, trans_summary = self.transformer.transform_batch(raw_batch)
        logger.info(f"[STAGE 3/5: TRANSFORM] Completed batch transformation across {len(transformed_batch)} datasets.")

        # Filter transformed batch for loading remaining datasets
        active_transformed_batch = {
            k: v for k, v in transformed_batch.items() if k.value not in completed_datasets_set
        }

        # Stage 4: Load Batch into PostgreSQL
        load_summary: Optional[LoadSummary] = None
        if session:
            logger.info("[STAGE 4/5: LOAD] Loading transformed datasets into PostgreSQL in foreign-key safe order...")
            load_summary = self.postgres_loader.load_batch(active_transformed_batch, session=session)
            logger.info(f"[STAGE 4/5: LOAD] Completed database loading ({load_summary.total_inserted:,} total rows inserted).")
        else:
            logger.info("[STAGE 4/5: LOAD] Database session omitted. Skipping database load.")

        # Track full checkpoint progress
        completed_sequence = list(raw_batch.keys())
        if self.checkpoint:
            self.checkpoint_manager.save_checkpoint(
                completed_datasets=completed_sequence,
                stage="LOAD",
                status="SUCCESS",
            )

        # Stage 5: Final Summary & Reporting
        logger.info("[STAGE 5/5: FINAL SUMMARY] Aggregating end-to-end pipeline metrics...")
        total_elapsed = time.perf_counter() - pipeline_start

        execution_order = [
            DatasetType.TRANSLATIONS,
            DatasetType.CUSTOMERS,
            DatasetType.PRODUCTS,
            DatasetType.ORDERS,
            DatasetType.ORDER_ITEMS,
            DatasetType.PAYMENTS,
            DatasetType.REVIEWS,
        ]
        actual_order = [d for d in execution_order if d in raw_batch]

        overall_status = "SUCCESS"
        if val_summary.overall_status == ValidationResult.FAILED or (
            load_summary and load_summary.total_inserted < load_summary.total_attempted
        ):
            overall_status = "FAILED"
        elif val_summary.overall_status == ValidationResult.WARNING:
            overall_status = "WARNING"

        # Remove checkpoint after a successful full run
        if self.checkpoint and overall_status in ("SUCCESS", "WARNING"):
            self.checkpoint_manager.clear_checkpoint()

        logger.info("=================================================================")
        logger.info(f"   ETL PIPELINE BATCH EXECUTION COMPLETE | Status: {overall_status}")
        logger.info(f"   Total Time: {total_elapsed:.4f}s | Datasets Processed: {len(actual_order)}")
        logger.info("=================================================================")

        return PipelineReport(
            extraction_summary=extraction_summary,
            validation_summary=val_summary,
            transformation_summary=trans_summary,
            load_summary=load_summary,
            total_execution_time_sec=round(total_elapsed, 4),
            overall_status=overall_status,
            execution_order=actual_order,
        )
