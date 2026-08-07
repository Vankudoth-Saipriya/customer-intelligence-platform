"""
Data Export utilities for saving DataFrames to CSV and Parquet file formats.
"""

from pathlib import Path
from typing import Union
from loguru import logger
import pandas as pd


class DataExporter:
    """
    Utility class for exporting DataFrames to standardized CSV and Parquet outputs.
    """

    @staticmethod
    def export_to_csv(
        df: pd.DataFrame,
        output_path: Union[str, Path],
        index: bool = False,
    ) -> Path:
        """
        Export pandas DataFrame to CSV format.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Exporting DataFrame ({len(df):,} rows) to CSV: '{path.resolve()}'")
        df.to_csv(path, index=index, encoding="utf-8")
        logger.info(f"Successfully exported CSV file: '{path.name}' ({path.stat().st_size / 1024.0:.2f} KB)")
        return path

    @staticmethod
    def export_to_parquet(
        df: pd.DataFrame,
        output_path: Union[str, Path],
        index: bool = False,
        compression: str = "snappy",
    ) -> Path:
        """
        Export pandas DataFrame to Apache Parquet format.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Exporting DataFrame ({len(df):,} rows) to Parquet: '{path.resolve()}'")
        df.to_parquet(path, index=index, compression=compression)
        logger.info(f"Successfully exported Parquet file: '{path.name}' ({path.stat().st_size / 1024.0:.2f} KB)")
        return path
