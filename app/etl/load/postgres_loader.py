"""
PostgreSQL Database Loader module for bulk population of OLTP domain models.

Provides batch insertion, schema field mapping verification, transaction management,
automatic rollback on failure, post-load verification, and foreign-key-safe sequence orchestration.
"""

import time
from typing import Any, Dict, List, Optional, Type, Union
from loguru import logger
import numpy as np
import pandas as pd
from sqlalchemy import func, inspect
from sqlalchemy.orm import Session

from app.etl.config import ETLSettings, etl_settings
from app.etl.load.report import LoadReport, LoadSummary
from app.etl.schemas.schema_registry import SchemaRegistry, schema_registry
from app.etl.utils.dataset_types import DatasetType
from app.etl.utils.exceptions import ETLLoadError
from app.models.domain import (
    CustomerModel,
    OrderItemModel,
    OrderModel,
    PaymentModel,
    ProductModel,
    ReviewModel,
)

# Mapping of DatasetType enum to target SQLAlchemy ORM Model classes
DATASET_MODEL_MAP: Dict[DatasetType, Type[Any]] = {
    DatasetType.CUSTOMERS: CustomerModel,
    DatasetType.PRODUCTS: ProductModel,
    DatasetType.ORDERS: OrderModel,
    DatasetType.ORDER_ITEMS: OrderItemModel,
    DatasetType.PAYMENTS: PaymentModel,
    DatasetType.REVIEWS: ReviewModel,
}

# Foreign-key safe insertion order
LOADING_SEQUENCE: List[DatasetType] = [
    DatasetType.CUSTOMERS,
    DatasetType.PRODUCTS,
    DatasetType.ORDERS,
    DatasetType.ORDER_ITEMS,
    DatasetType.PAYMENTS,
    DatasetType.REVIEWS,
]


class PostgresLoader:
    """
    Database loader orchestrating initial full population into PostgreSQL.
    """

    def __init__(
        self,
        batch_size: Optional[int] = None,
        registry: Optional[SchemaRegistry] = None,
        settings: Optional[ETLSettings] = None,
    ) -> None:
        """
        Initialize PostgresLoader with batch size configuration.

        Args:
            batch_size: Number of records per bulk insert chunk. Defaults to settings.BATCH_SIZE.
            registry: SchemaRegistry instance. Defaults to global schema_registry.
            settings: ETL configuration instance. Defaults to application etl_settings.
        """
        self.settings = settings or etl_settings
        self.batch_size = batch_size or self.settings.BATCH_SIZE
        self.registry = registry or schema_registry

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
            raise ETLLoadError(
                message=f"Unsupported or unregistered dataset identifier: '{dataset}'",
                details=f"Allowed values: {[d.value for d in DatasetType]}",
            )

    def _get_orm_column_names(self, model_cls: Type[Any]) -> List[str]:
        """
        Extract list of persistent database column names for an ORM model class.
        """
        mapper = inspect(model_cls)
        return [c.key for c in mapper.column_attrs]

    def _prepare_records(self, df: pd.DataFrame, model_cols: List[str]) -> List[Dict[str, Any]]:
        """
        Filter DataFrame columns to model fields and replace pandas NaN/NaT with Python None.
        """
        persisted_df = df[[col for col in df.columns if col in model_cols]].copy()

        records = persisted_df.to_dict(orient="records")
        clean_records: List[Dict[str, Any]] = []
        for record in records:
            clean_rec = {}
            for k, v in record.items():
                if pd.isna(v):
                    clean_rec[k] = None
                else:
                    clean_rec[k] = v
            clean_records.append(clean_rec)
        return clean_records

    def load_dataset(
        self,
        dataset: Union[DatasetType, str],
        df: pd.DataFrame,
        session: Session,
    ) -> LoadReport:
        """
        Load a single dataset DataFrame into PostgreSQL via SQLAlchemy Session with post-load verification.

        Args:
            dataset: DatasetType enum or string identifier.
            df: Input dataset pandas DataFrame.
            session: Active SQLAlchemy Session instance.

        Returns:
            LoadReport containing total attempted, inserted, skipped rows, verification status, and execution time.

        Raises:
            ETLLoadError: If database insertion or post-load count verification fails.
        """
        start_time = time.perf_counter()
        d_type = self._resolve_dataset_type(dataset)
        rows_attempted = len(df)
        warnings: List[str] = []

        logger.info(f"Initiating database load for dataset: '{d_type.value}' ({rows_attempted:,} rows)")

        # Handle reference tables not persisted to OLTP schema (e.g. translations)
        if d_type not in DATASET_MODEL_MAP:
            warn_msg = f"Dataset '{d_type.value}' has no target OLTP database table. Skipping database insertion."
            logger.warning(warn_msg)
            warnings.append(warn_msg)
            elapsed_sec = time.perf_counter() - start_time
            return LoadReport(
                dataset=d_type,
                rows_attempted=rows_attempted,
                rows_inserted=0,
                rows_skipped=rows_attempted,
                execution_time_sec=round(elapsed_sec, 4),
                verified=True,
                verification_message="Skipped database insertion (reference dataset).",
                verification_time_sec=0.0,
                warnings=warnings,
                statistics={"status": "SKIPPED_NO_MODEL"},
            )

        model_cls = DATASET_MODEL_MAP[d_type]
        model_cols = self._get_orm_column_names(model_cls)

        ignored_cols = [c for c in df.columns if c not in model_cols]
        if ignored_cols:
            logger.info(f"Dataset '{d_type.value}' contains {len(ignored_cols)} intermediate columns ignored during insertion: {ignored_cols}")

        records = self._prepare_records(df, model_cols)
        rows_inserted = 0

        try:
            total_batches = (len(records) + self.batch_size - 1) // self.batch_size if records else 0
            logger.info(f"Loading '{d_type.value}' in {total_batches} batches of size {self.batch_size}...")

            for i in range(0, len(records), self.batch_size):
                batch = records[i : i + self.batch_size]
                session.bulk_insert_mappings(model_cls, batch)
                rows_inserted += len(batch)
                batch_num = (i // self.batch_size) + 1
                if batch_num % 10 == 0 or batch_num == total_batches:
                    logger.debug(f"Loaded batch {batch_num}/{total_batches} for '{d_type.value}' ({rows_inserted:,} rows committed so far)")

            session.commit()

            # -----------------------------------------------------------------
            # Post-load Count Verification
            # -----------------------------------------------------------------
            v_start = time.perf_counter()
            db_row_count = session.query(func.count()).select_from(model_cls).scalar() or 0
            v_time = round(time.perf_counter() - v_start, 4)

            if db_row_count < rows_inserted:
                error_msg = (
                    f"Post-load verification failed for dataset '{d_type.value}': "
                    f"Expected at least {rows_inserted} rows in table '{model_cls.__tablename__}', found {db_row_count}."
                )
                logger.error(error_msg)
                raise ETLLoadError(
                    message=error_msg,
                    details=f"Table '{model_cls.__tablename__}' row count: {db_row_count}, Expected inserted: {rows_inserted}",
                )

            verified = True
            verification_msg = f"Successfully verified {db_row_count:,} total rows present in database table '{model_cls.__tablename__}'."
            logger.info(f"Post-load verification passed for dataset '{d_type.value}' in {v_time:.4f}s.")

        except ETLLoadError:
            raise
        except Exception as exc:
            session.rollback()
            error_msg = f"Failed to load dataset '{d_type.value}' into database: {str(exc)}"
            logger.error(error_msg)
            raise ETLLoadError(
                message=error_msg,
                details=f"Rolled back transaction. Attempted: {rows_attempted}, Inserted before failure: {rows_inserted}. Error: {str(exc)}",
            ) from exc

        elapsed_sec = time.perf_counter() - start_time
        logger.info(
            f"Successfully loaded '{d_type.value}' into PostgreSQL in {elapsed_sec:.4f}s | "
            f"Inserted: {rows_inserted:,}/{rows_attempted:,} rows | Verified: {verified}"
        )

        return LoadReport(
            dataset=d_type,
            rows_attempted=rows_attempted,
            rows_inserted=rows_inserted,
            rows_skipped=0,
            execution_time_sec=round(elapsed_sec, 4),
            verified=verified,
            verification_message=verification_msg,
            verification_time_sec=v_time,
            warnings=warnings,
            statistics={
                "batch_size": self.batch_size,
                "total_batches": total_batches,
                "table_name": model_cls.__tablename__,
                "db_total_row_count": db_row_count,
                "ignored_intermediate_columns": ignored_cols,
            },
        )

    def load_batch(
        self,
        datasets: Dict[Union[DatasetType, str], pd.DataFrame],
        session: Session,
    ) -> LoadSummary:
        """
        Load an entire batch of DataFrames into PostgreSQL in foreign-key safe order with post-load verification.

        Args:
            datasets: Dictionary mapping DatasetType or string keys to DataFrames.
            session: Active SQLAlchemy Session instance.

        Returns:
            LoadSummary aggregating reports across all datasets loaded.
        """
        start_time = time.perf_counter()
        logger.info(f"Initiating foreign-key safe batch load across {len(datasets)} datasets...")

        resolved_batch: Dict[DatasetType, pd.DataFrame] = {}
        for k, v in datasets.items():
            resolved_batch[self._resolve_dataset_type(k)] = v

        reports: Dict[DatasetType, LoadReport] = {}
        total_attempted = 0
        total_inserted = 0
        total_skipped = 0

        # Execute load in strict foreign-key safe sequence
        for d_type in LOADING_SEQUENCE:
            if d_type in resolved_batch:
                df = resolved_batch[d_type]
                report = self.load_dataset(d_type, df, session=session)
                reports[d_type] = report
                total_attempted += report.rows_attempted
                total_inserted += report.rows_inserted
                total_skipped += report.rows_skipped

        # Handle any remaining datasets not in standard sequence (e.g. translations)
        for d_type, df in resolved_batch.items():
            if d_type not in reports:
                report = self.load_dataset(d_type, df, session=session)
                reports[d_type] = report
                total_attempted += report.rows_attempted
                total_inserted += report.rows_inserted
                total_skipped += report.rows_skipped

        total_elapsed = time.perf_counter() - start_time
        summary = LoadSummary(
            reports=reports,
            total_datasets=len(reports),
            total_attempted=total_attempted,
            total_inserted=total_inserted,
            total_skipped=total_skipped,
            total_execution_time_sec=round(total_elapsed, 4),
        )

        logger.info(
            f"Completed foreign-key safe batch load across {len(reports)} datasets in {total_elapsed:.4f}s | "
            f"Total Inserted: {total_inserted:,}/{total_attempted:,} rows | All Verified: {summary.is_verified()}"
        )
        return summary
