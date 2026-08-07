"""
Data Profiling utilities for dataset diagnostics and exploratory analysis.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union
from loguru import logger
import numpy as np
import pandas as pd

from app.etl.utils.dataset_types import DatasetType


class DataProfiler:
    """
    Automated dataset profiler evaluating structural, missing, numeric, and categorical properties.
    """

    @staticmethod
    def dataset_overview(df: pd.DataFrame) -> Dict[str, Any]:
        """
        Extract high-level dataset structural statistics (shape, memory, column counts).
        """
        memory_mb = round(df.memory_usage(deep=True).sum() / (1024.0 * 1024.0), 3)
        return {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "shape": list(df.shape),
            "memory_mb": memory_mb,
        }

    @staticmethod
    def missing_value_summary(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate per-column missing value counts and percentages.
        """
        null_counts = df.isnull().sum()
        null_percents = (null_counts / len(df) * 100.0).round(2) if len(df) > 0 else 0.0
        summary_df = pd.DataFrame(
            {
                "column": df.columns,
                "missing_count": null_counts.values,
                "missing_percent": null_percents.values,
                "dtype": df.dtypes.astype(str).values,
            }
        ).sort_values(by="missing_count", ascending=False).reset_index(drop=True)
        return summary_df

    @staticmethod
    def duplicate_summary(df: pd.DataFrame, key_cols: list = None) -> Dict[str, Any]:
        """
        Summarize exact duplicate row counts and optional primary key duplicates.
        """
        exact_dups = int(df.duplicated().sum())
        key_dups = 0
        if key_cols and all(k in df.columns for k in key_cols):
            key_dups = int(df.duplicated(subset=key_cols).sum())

        return {
            "total_rows": len(df),
            "exact_duplicate_rows": exact_dups,
            "exact_duplicate_percent": round((exact_dups / len(df) * 100.0), 2) if len(df) > 0 else 0.0,
            "key_columns": key_cols,
            "key_duplicate_rows": key_dups,
        }

    @staticmethod
    def numeric_statistics(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate descriptive statistics for numeric columns (mean, std, min, quantiles, skew).
        """
        num_cols = df.select_dtypes(include=[np.number]).columns
        if len(num_cols) == 0:
            return pd.DataFrame()

        desc = df[num_cols].describe().T
        desc["skewness"] = df[num_cols].skew().round(4)
        desc["null_count"] = df[num_cols].isnull().sum()
        return desc.reset_index().rename(columns={"index": "column"})

    @staticmethod
    def categorical_statistics(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate descriptive statistics for categorical/string columns.
        """
        cat_cols = df.select_dtypes(include=["object", "string", "category"]).columns
        if len(cat_cols) == 0:
            return pd.DataFrame()

        records = []
        for col in cat_cols:
            series = df[col].dropna()
            unique_cnt = series.nunique()
            top_val = series.mode().iloc[0] if not series.empty else None
            top_freq = int((series == top_val).sum()) if top_val is not None else 0
            records.append(
                {
                    "column": col,
                    "unique_count": unique_cnt,
                    "top_value": str(top_val) if top_val is not None else None,
                    "top_frequency": top_freq,
                    "top_percent": round((top_freq / len(df) * 100.0), 2) if len(df) > 0 else 0.0,
                    "null_count": int(df[col].isnull().sum()),
                }
            )
        return pd.DataFrame(records)

    @staticmethod
    def data_type_summary(df: pd.DataFrame) -> pd.DataFrame:
        """
        Summarize column data types across the dataset.
        """
        return pd.DataFrame(
            {
                "column": df.columns,
                "data_type": df.dtypes.astype(str).values,
                "non_null_count": df.notnull().sum().values,
                "null_count": df.isnull().sum().values,
            }
        )

    def profile_full(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute comprehensive profiling suite across a DataFrame.
        """
        logger.info(f"Generating full data profile for DataFrame shape {df.shape}...")
        return {
            "overview": self.dataset_overview(df),
            "missing_values": self.missing_value_summary(df),
            "duplicates": self.duplicate_summary(df),
            "numeric_stats": self.numeric_statistics(df),
            "categorical_stats": self.categorical_statistics(df),
            "data_types": self.data_type_summary(df),
        }

    def generate_profile_report(
        self,
        df: pd.DataFrame,
        dataset_name: Union[DatasetType, str],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Generate and persist a JSON data profile report artifact for a dataset.

        Args:
            df: Input dataset pandas DataFrame.
            dataset_name: Dataset identifier string or DatasetType enum.
            output_dir: Destination folder path. Defaults to artifacts/profiles/.

        Returns:
            Path to the saved JSON profile report artifact.
        """
        name_str = dataset_name.value if isinstance(dataset_name, DatasetType) else str(dataset_name).lower()
        if name_str.endswith("_profile.json"):
            name_str = name_str.replace("_profile.json", "")
        elif name_str.endswith(".csv"):
            name_str = name_str.replace(".csv", "")

        filename = f"{name_str}_profile.json"

        if output_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            target_dir = project_root / "artifacts" / "profiles"
        else:
            target_dir = Path(output_dir)

        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / filename

        logger.info(f"Generating profile report for dataset '{name_str}' -> '{target_path}'...")
        profile = self.profile_full(df)

        report_json = {
            "dataset_name": name_str,
            "overview": profile["overview"],
            "missing_values": profile["missing_values"].to_dict(orient="records") if isinstance(profile["missing_values"], pd.DataFrame) else profile["missing_values"],
            "duplicates": profile["duplicates"],
            "numeric_statistics": profile["numeric_stats"].to_dict(orient="records") if isinstance(profile["numeric_stats"], pd.DataFrame) else profile["numeric_stats"],
            "categorical_statistics": profile["categorical_stats"].to_dict(orient="records") if isinstance(profile["categorical_stats"], pd.DataFrame) else profile["categorical_stats"],
            "data_types": profile["data_types"].to_dict(orient="records") if isinstance(profile["data_types"], pd.DataFrame) else profile["data_types"],
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(report_json, f, indent=2, default=str)

        logger.info(f"Successfully generated profile report artifact: '{target_path.name}'")
        return target_path

    def generate_batch_profiles(
        self,
        datasets: Dict[Union[DatasetType, str], pd.DataFrame],
        output_dir: Optional[Union[str, Path]] = None,
    ) -> Dict[str, Path]:
        """
        Generate and persist profile reports across a batch dictionary of DataFrames.

        Args:
            datasets: Dictionary mapping dataset names or DatasetType to DataFrames.
            output_dir: Destination folder path. Defaults to artifacts/profiles/.

        Returns:
            Dictionary mapping dataset names to saved profile report Paths.
        """
        logger.info(f"Generating batch profile reports across {len(datasets)} datasets...")
        result_paths: Dict[str, Path] = {}
        for d_name, df in datasets.items():
            name_key = d_name.value if isinstance(d_name, DatasetType) else str(d_name)
            report_path = self.generate_profile_report(df, name_key, output_dir=output_dir)
            result_paths[name_key] = report_path
        return result_paths
