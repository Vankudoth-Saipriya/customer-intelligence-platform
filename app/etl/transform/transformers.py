"""
ETL Data Transformation Engine for cleansing, standardizing, and operational derivations.

Applies generic schema-driven transformations and dataset-specific business logic
to produce operational ETL-derived fields and detailed TransformationReports.
"""

import time
from typing import Any, Dict, List, Optional, Tuple, Union
from loguru import logger
import numpy as np
import pandas as pd

from app.etl.config import ETLSettings, etl_settings
from app.etl.schemas.base_schema import DatasetSchema
from app.etl.schemas.schema_registry import SchemaRegistry, schema_registry
from app.etl.transform.report import (
    TransformationReport,
    TransformationStep,
    TransformationSummary,
)
from app.etl.utils.dataset_types import DatasetType
from app.etl.utils.exceptions import ETLTransformationError


class DataTransformer:
    """
    Transformation engine for data cleansing, standardization, and operational derivations.
    """

    def __init__(
        self,
        registry: Optional[SchemaRegistry] = None,
        settings: Optional[ETLSettings] = None,
    ) -> None:
        """
        Initialize DataTransformer with SchemaRegistry and ETLSettings.

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
            raise ETLTransformationError(
                message=f"Unsupported or unregistered dataset identifier: '{dataset}'",
                details=f"Allowed values: {[d.value for d in DatasetType]}",
            )

    # -------------------------------------------------------------------------
    # Reusable Generic Transformations
    # -------------------------------------------------------------------------

    def _apply_missing_value_standardization(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        t0 = time.perf_counter()
        steps: List[TransformationStep] = []
        string_cols = df.select_dtypes(include=["object", "string"]).columns
        if len(string_cols) > 0:
            missing_variants = ["", "null", "NULL", "None", "NONE", "NaN", "nan", "N/A", "n/a"]
            before_nulls = df[string_cols].isnull().sum().sum()
            for col in string_cols:
                df[col] = df[col].replace(missing_variants, np.nan)
            after_nulls = df[string_cols].isnull().sum().sum()
            affected = int(after_nulls - before_nulls)
            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)

            steps.append(
                TransformationStep(
                    step_name="missing_value_standardization",
                    description=f"Standardized string missing value variants across {len(string_cols)} columns.",
                    affected_rows=max(affected, 0),
                    columns_modified=list(string_cols),
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )
        return df, steps

    def _apply_string_cleansing(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        t0 = time.perf_counter()
        steps: List[TransformationStep] = []
        string_cols = df.select_dtypes(include=["object", "string"]).columns
        modified_cols: List[str] = []
        affected_rows = 0

        for col in string_cols:
            non_null_mask = df[col].notnull()
            if non_null_mask.any():
                original = df.loc[non_null_mask, col].astype(str)
                trimmed = original.str.strip()
                changed = (original != trimmed).sum()
                if changed > 0:
                    affected_rows += int(changed)
                    modified_cols.append(col)
                df.loc[non_null_mask, col] = trimmed

        exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        if string_cols.size > 0:
            steps.append(
                TransformationStep(
                    step_name="string_cleansing",
                    description=f"Trimmed leading/trailing whitespace across {len(string_cols)} string columns.",
                    affected_rows=affected_rows,
                    columns_modified=modified_cols if modified_cols else list(string_cols),
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )
        return df, steps

    def _apply_date_conversions(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        t0 = time.perf_counter()
        steps: List[TransformationStep] = []
        converted_cols: List[str] = []
        for col in schema.date_fields:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
                converted_cols.append(col)
        exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        if converted_cols:
            steps.append(
                TransformationStep(
                    step_name="date_conversions",
                    description=f"Converted timestamp columns to datetime: {converted_cols}.",
                    affected_rows=len(df),
                    columns_modified=converted_cols,
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )
        return df, steps

    def _apply_numeric_conversions(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        t0 = time.perf_counter()
        steps: List[TransformationStep] = []
        converted_cols: List[str] = []
        for col in schema.numeric_constraints.keys():
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                converted_cols.append(col)
        exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        if converted_cols:
            steps.append(
                TransformationStep(
                    step_name="numeric_conversions",
                    description=f"Converted columns to numeric values: {converted_cols}.",
                    affected_rows=len(df),
                    columns_modified=converted_cols,
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )
        return df, steps

    def _apply_deduplication(
        self, df: pd.DataFrame, schema: DatasetSchema
    ) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        t0 = time.perf_counter()
        steps: List[TransformationStep] = []
        initial_len = len(df)
        df = df.drop_duplicates().reset_index(drop=True)
        dropped = initial_len - len(df)
        exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        if dropped > 0:
            steps.append(
                TransformationStep(
                    step_name="deduplication",
                    description=f"Removed {dropped:,} exact duplicate rows.",
                    affected_rows=dropped,
                    columns_modified=list(df.columns),
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )
        return df, steps

    # -------------------------------------------------------------------------
    # Dataset-Specific Transformations
    # -------------------------------------------------------------------------

    def _transform_customers_specific(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        steps: List[TransformationStep] = []

        # 1. Normalize city names
        if "customer_city" in df.columns:
            t0 = time.perf_counter()
            df["customer_city"] = (
                df["customer_city"]
                .fillna("unknown")
                .astype(str)
                .str.strip()
                .str.title()
            )
            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            steps.append(
                TransformationStep(
                    step_name="customers_normalize_city",
                    description="Normalized customer city names to Title Case.",
                    affected_rows=len(df),
                    columns_modified=["customer_city"],
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        # 2. Normalize state codes
        if "customer_state" in df.columns:
            t0 = time.perf_counter()
            df["customer_state"] = (
                df["customer_state"]
                .fillna("XX")
                .astype(str)
                .str.strip()
                .str.upper()
            )
            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            steps.append(
                TransformationStep(
                    step_name="customers_normalize_state",
                    description="Normalized customer state codes to 2-letter Uppercase.",
                    affected_rows=len(df),
                    columns_modified=["customer_state"],
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        # 3. Standardize ZIP prefix format (5-digit zero-padding)
        if "customer_zip_code_prefix" in df.columns:
            t0 = time.perf_counter()
            df["customer_zip_code_prefix"] = (
                pd.to_numeric(df["customer_zip_code_prefix"], errors="coerce")
                .fillna(0)
                .astype(int)
                .astype(str)
                .str.zfill(5)
            )
            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            steps.append(
                TransformationStep(
                    step_name="customers_standardize_zip",
                    description="Standardized customer zip code prefix format to 5-digit zero-padded strings.",
                    affected_rows=len(df),
                    columns_modified=["customer_zip_code_prefix"],
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        return df, steps

    def _transform_orders_specific(
        self,
        df: pd.DataFrame,
        context_dfs: Optional[Dict[DatasetType, pd.DataFrame]] = None,
    ) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        steps: List[TransformationStep] = []

        p_date = pd.to_datetime(df["order_purchase_timestamp"], errors="coerce", utc=True) if "order_purchase_timestamp" in df.columns else None
        c_date = pd.to_datetime(df["order_delivered_carrier_date"], errors="coerce", utc=True) if "order_delivered_carrier_date" in df.columns else None
        d_date = pd.to_datetime(df["order_delivered_customer_date"], errors="coerce", utc=True) if "order_delivered_customer_date" in df.columns else None
        e_date = pd.to_datetime(df["order_estimated_delivery_date"], errors="coerce", utc=True) if "order_estimated_delivery_date" in df.columns else None

        # 1. Calculate delivery_delay_days
        if d_date is not None and e_date is not None:
            t0 = time.perf_counter()
            delay_td = d_date - e_date
            df["delivery_delay_days"] = np.where(
                d_date.notnull(),
                delay_td.dt.total_seconds() / (24.0 * 3600.0),
                np.nan,
            )
            df["delivery_delay_days"] = df["delivery_delay_days"].round(2)
            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            affected = int(df["delivery_delay_days"].notnull().sum())
            steps.append(
                TransformationStep(
                    step_name="orders_calc_delivery_delay_days",
                    description="Calculated operational 'delivery_delay_days' (delivered_customer_date - estimated_delivery_date).",
                    affected_rows=affected,
                    columns_modified=["delivery_delay_days"],
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        # 2. Calculate fulfillment_days / order_processing_days
        if c_date is not None and p_date is not None:
            t0 = time.perf_counter()
            ful_td = c_date - p_date
            df["fulfillment_days"] = np.where(
                c_date.notnull(),
                ful_td.dt.total_seconds() / (24.0 * 3600.0),
                np.nan,
            )
            df["fulfillment_days"] = df["fulfillment_days"].round(2)
            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            affected = int(df["fulfillment_days"].notnull().sum())
            steps.append(
                TransformationStep(
                    step_name="orders_calc_fulfillment_days",
                    description="Calculated operational 'fulfillment_days' (delivered_carrier_date - purchase_timestamp).",
                    affected_rows=affected,
                    columns_modified=["fulfillment_days"],
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        # 3. Calculate delivery_days
        if d_date is not None and p_date is not None:
            t0 = time.perf_counter()
            del_td = d_date - p_date
            df["delivery_days"] = np.where(
                d_date.notnull(),
                del_td.dt.total_seconds() / (24.0 * 3600.0),
                np.nan,
            )
            df["delivery_days"] = df["delivery_days"].round(2)
            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            affected = int(df["delivery_days"].notnull().sum())
            steps.append(
                TransformationStep(
                    step_name="orders_calc_delivery_days",
                    description="Calculated operational 'delivery_days' (delivered_customer_date - purchase_timestamp).",
                    affected_rows=affected,
                    columns_modified=["delivery_days"],
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        # 4. Operational flags: is_delivered & is_late_delivery
        if "order_status" in df.columns or (d_date is not None and e_date is not None):
            t0 = time.perf_counter()
            mod_cols: List[str] = []
            if "order_status" in df.columns:
                df["is_delivered"] = df["order_status"].astype(str).str.lower() == "delivered"
                mod_cols.append("is_delivered")

            if d_date is not None and e_date is not None:
                df["is_late_delivery"] = np.where(
                    d_date.notnull(),
                    d_date > e_date,
                    False,
                )
                mod_cols.append("is_late_delivery")

            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            steps.append(
                TransformationStep(
                    step_name="orders_operational_flags",
                    description="Created operational boolean flags 'is_delivered' and 'is_late_delivery'.",
                    affected_rows=len(df),
                    columns_modified=mod_cols,
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        # 5. Order header line items aggregations
        if context_dfs and DatasetType.ORDER_ITEMS in context_dfs:
            t0 = time.perf_counter()
            items_df = context_dfs[DatasetType.ORDER_ITEMS]
            if "order_id" in items_df.columns and "price" in items_df.columns and "freight_value" in items_df.columns:
                agg_df = items_df.groupby("order_id").agg(
                    order_items_qty=("order_item_id", "count"),
                    total_items_price=("price", "sum"),
                    total_freight_value=("freight_value", "sum"),
                ).reset_index()
                agg_df["order_value"] = agg_df["total_items_price"] + agg_df["total_freight_value"]
                agg_df = agg_df.round(2)

                df = df.merge(agg_df, on="order_id", how="left")
                df["order_items_qty"] = df["order_items_qty"].fillna(0).astype(int)
                df["total_items_price"] = df["total_items_price"].fillna(0.0)
                df["total_freight_value"] = df["total_freight_value"].fillna(0.0)
                df["order_value"] = df["order_value"].fillna(0.0)
                exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
                steps.append(
                    TransformationStep(
                        step_name="orders_aggregate_line_items",
                        description="Aggregated line items into operational fields: order_items_qty, total_items_price, total_freight_value, order_value.",
                        affected_rows=len(agg_df),
                        columns_modified=["order_items_qty", "total_items_price", "total_freight_value", "order_value"],
                        execution_time_ms=exec_ms,
                        status="SUCCESS",
                    )
                )

        return df, steps

    def _transform_products_specific(
        self,
        df: pd.DataFrame,
        context_dfs: Optional[Dict[DatasetType, pd.DataFrame]] = None,
    ) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        steps: List[TransformationStep] = []

        # 1. Merge English category translations
        if context_dfs and DatasetType.TRANSLATIONS in context_dfs and "product_category_name" in df.columns:
            t0 = time.perf_counter()
            trans_df = context_dfs[DatasetType.TRANSLATIONS]
            if "product_category_name" in trans_df.columns and "product_category_name_english" in trans_df.columns:
                trans_map = dict(zip(trans_df["product_category_name"], trans_df["product_category_name_english"]))
                df["category_name_english"] = df["product_category_name"].map(trans_map).fillna("Uncategorized").astype(str).str.title()
                exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
                mapped_cnt = int((df["category_name_english"] != "Uncategorized").sum())
                steps.append(
                    TransformationStep(
                        step_name="products_merge_translations",
                        description="Merged English product category translations ('category_name_english').",
                        affected_rows=mapped_cnt,
                        columns_modified=["category_name_english"],
                        execution_time_ms=exec_ms,
                        status="SUCCESS",
                    )
                )
        elif "category_name_english" not in df.columns:
            df["category_name_english"] = "Uncategorized"

        # 2. Compute product_volume_cm3 & volumetric_weight_g
        dim_cols = ["product_length_cm", "product_height_cm", "product_width_cm"]
        if all(c in df.columns for c in dim_cols):
            t0 = time.perf_counter()
            l = pd.to_numeric(df["product_length_cm"], errors="coerce")
            h = pd.to_numeric(df["product_height_cm"], errors="coerce")
            w = pd.to_numeric(df["product_width_cm"], errors="coerce")

            df["product_volume_cm3"] = (l * h * w).round(2)
            df["volumetric_weight_g"] = (df["product_volume_cm3"] / 6.0).round(2)
            exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            affected = int(df["product_volume_cm3"].notnull().sum())
            steps.append(
                TransformationStep(
                    step_name="products_calc_volumetric_weight",
                    description="Computed operational product dimension volume ('product_volume_cm3') and volumetric weight ('volumetric_weight_g').",
                    affected_rows=affected,
                    columns_modified=["product_volume_cm3", "volumetric_weight_g"],
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        return df, steps

    def _transform_payments_specific(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        steps: List[TransformationStep] = []
        mod_cols: List[str] = []
        t0 = time.perf_counter()

        # 1. Create is_installment_payment boolean
        if "payment_installments" in df.columns:
            inst = pd.to_numeric(df["payment_installments"], errors="coerce").fillna(1)
            df["is_installment_payment"] = inst > 1
            mod_cols.append("is_installment_payment")

        # 2. Create is_voucher_payment boolean
        if "payment_type" in df.columns:
            df["is_voucher_payment"] = df["payment_type"].astype(str).str.lower() == "voucher"
            mod_cols.append("is_voucher_payment")

        exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        if mod_cols:
            steps.append(
                TransformationStep(
                    step_name="payments_operational_flags",
                    description="Created operational boolean flags 'is_installment_payment' and 'is_voucher_payment'.",
                    affected_rows=len(df),
                    columns_modified=mod_cols,
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        return df, steps

    def _transform_reviews_specific(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[TransformationStep]]:
        steps: List[TransformationStep] = []
        mod_cols: List[str] = []
        t0 = time.perf_counter()

        # 1. Create has_comment_title boolean
        if "review_comment_title" in df.columns:
            t = df["review_comment_title"]
            df["has_comment_title"] = t.notnull() & t.astype(str).str.strip().ne("")
            mod_cols.append("has_comment_title")

        # 2. Create has_comment_message boolean
        if "review_comment_message" in df.columns:
            m = df["review_comment_message"]
            df["has_comment_message"] = m.notnull() & m.astype(str).str.strip().ne("")
            mod_cols.append("has_comment_message")

        exec_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        if mod_cols:
            steps.append(
                TransformationStep(
                    step_name="reviews_operational_flags",
                    description="Created operational boolean flags 'has_comment_title' and 'has_comment_message'.",
                    affected_rows=len(df),
                    columns_modified=mod_cols,
                    execution_time_ms=exec_ms,
                    status="SUCCESS",
                )
            )

        return df, steps

    # -------------------------------------------------------------------------
    # Public Transformation Methods
    # -------------------------------------------------------------------------

    def transform_dataset(
        self,
        dataset: Union[DatasetType, str],
        df: pd.DataFrame,
        context_dfs: Optional[Dict[Union[DatasetType, str], pd.DataFrame]] = None,
    ) -> Tuple[pd.DataFrame, TransformationReport]:
        """
        Transform a single dataset DataFrame by applying generic cleansing and domain derivations.

        Args:
            dataset: DatasetType enum or dataset name string.
            df: Input dataset pandas DataFrame.
            context_dfs: Optional dictionary of context DataFrames for joins/aggregations.

        Returns:
            Tuple of (transformed_df, TransformationReport).

        Raises:
            ETLTransformationError: If dataset transformation fails.
        """
        start_time = time.perf_counter()
        d_type = self._resolve_dataset_type(dataset)
        initial_rows = len(df)
        logger.info(f"Initiating transformation for dataset: '{d_type.value}' ({initial_rows:,} rows)")

        schema = self.registry.get(d_type.value)
        out_df = df.copy()
        all_steps: List[TransformationStep] = []
        warnings: List[str] = []

        resolved_context: Dict[DatasetType, pd.DataFrame] = {}
        if context_dfs:
            for k, v in context_dfs.items():
                resolved_context[self._resolve_dataset_type(k)] = v

        try:
            # 1. Generic Schema-Driven Cleansing
            out_df, s_std = self._apply_missing_value_standardization(out_df, schema)
            all_steps.extend(s_std)

            out_df, s_str = self._apply_string_cleansing(out_df, schema)
            all_steps.extend(s_str)

            out_df, s_date = self._apply_date_conversions(out_df, schema)
            all_steps.extend(s_date)

            out_df, s_num = self._apply_numeric_conversions(out_df, schema)
            all_steps.extend(s_num)

            out_df, s_dedup = self._apply_deduplication(out_df, schema)
            all_steps.extend(s_dedup)

            # 2. Dataset-Specific Transformations
            spec_steps: List[TransformationStep] = []
            if d_type == DatasetType.CUSTOMERS:
                out_df, spec_steps = self._transform_customers_specific(out_df)
            elif d_type == DatasetType.ORDERS:
                out_df, spec_steps = self._transform_orders_specific(out_df, resolved_context)
            elif d_type == DatasetType.PRODUCTS:
                out_df, spec_steps = self._transform_products_specific(out_df, resolved_context)
            elif d_type == DatasetType.PAYMENTS:
                out_df, spec_steps = self._transform_payments_specific(out_df)
            elif d_type == DatasetType.REVIEWS:
                out_df, spec_steps = self._transform_reviews_specific(out_df)

            all_steps.extend(spec_steps)

        except Exception as exc:
            error_msg = f"Failed to execute transformations on dataset '{d_type.value}': {str(exc)}"
            logger.error(error_msg)
            raise ETLTransformationError(message=error_msg, details=str(exc)) from exc

        elapsed_sec = time.perf_counter() - start_time
        final_rows = len(out_df)

        transformations_applied = [
            f"{s.step_name}: {s.description}" for s in all_steps
        ]

        report = TransformationReport(
            dataset=d_type,
            rows_processed=final_rows,
            transformations_applied=transformations_applied,
            steps=all_steps,
            execution_time_sec=round(elapsed_sec, 4),
            warnings=warnings,
            statistics={
                "initial_rows": initial_rows,
                "final_rows": final_rows,
                "rows_dropped": initial_rows - final_rows,
                "total_steps": len(all_steps),
                "total_rows_modified": sum(s.affected_rows for s in all_steps),
            },
        )

        logger.info(
            f"Completed transformation for '{d_type.value}' in {elapsed_sec:.4f}s | "
            f"Final Rows: {final_rows:,} | Total Steps: {len(all_steps)} | Modified Rows: {report.total_rows_modified():,}"
        )
        return out_df, report

    def transform_batch(
        self, datasets: Dict[Union[DatasetType, str], pd.DataFrame]
    ) -> Tuple[Dict[DatasetType, pd.DataFrame], TransformationSummary]:
        """
        Transform an entire batch of dataset DataFrames in topological dependency order.

        Args:
            datasets: Dictionary mapping DatasetType or dataset names to DataFrames.

        Returns:
            Tuple of (transformed_datasets_dict, TransformationSummary).
        """
        start_time = time.perf_counter()
        logger.info(f"Initiating batch transformation across {len(datasets)} datasets...")

        resolved_batch: Dict[DatasetType, pd.DataFrame] = {}
        for k, v in datasets.items():
            resolved_batch[self._resolve_dataset_type(k)] = v

        transformed_dict: Dict[DatasetType, pd.DataFrame] = {}
        reports: Dict[DatasetType, TransformationReport] = {}

        transform_order = [
            DatasetType.TRANSLATIONS,
            DatasetType.CUSTOMERS,
            DatasetType.PRODUCTS,
            DatasetType.ORDER_ITEMS,
            DatasetType.ORDERS,
            DatasetType.PAYMENTS,
            DatasetType.REVIEWS,
        ]

        for d_type in transform_order:
            if d_type in resolved_batch:
                df = resolved_batch[d_type]
                context = {**resolved_batch, **transformed_dict}
                trans_df, report = self.transform_dataset(d_type, df, context_dfs=context)
                transformed_dict[d_type] = trans_df
                reports[d_type] = report

        total_elapsed = time.perf_counter() - start_time
        summary = TransformationSummary(
            reports=reports,
            total_datasets=len(reports),
            total_execution_time_sec=round(total_elapsed, 4),
        )

        logger.info(
            f"Completed batch transformation across {len(reports)} datasets in {total_elapsed:.4f}s."
        )
        return transformed_dict, summary
