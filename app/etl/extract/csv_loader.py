"""
Raw CSV file extraction module for Customer Intelligence Platform.

Provides robust loading, file existence validation, required column verification,
UTF-8 encoding support, and loading statistics logging for all raw CSV datasets.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
from loguru import logger
import pandas as pd

from app.etl.config import ETLSettings, etl_settings
from app.etl.utils.constants import (
    RAW_CUSTOMERS_CSV,
    RAW_DATASETS,
    RAW_GEOLOCATION_CSV,
    RAW_ORDER_ITEMS_CSV,
    RAW_ORDER_PAYMENTS_CSV,
    RAW_ORDER_REVIEWS_CSV,
    RAW_ORDERS_CSV,
    RAW_PRODUCTS_CSV,
    RAW_SELLERS_CSV,
    RAW_TRANSLATIONS_CSV,
    REQUIRED_COLUMNS,
)
from app.etl.utils.dataset_types import DatasetType
from app.etl.utils.exceptions import ETLExtractionError

DATASET_FILENAME_MAP: Dict[str, str] = {
    "customers": RAW_CUSTOMERS_CSV,
    "orders": RAW_ORDERS_CSV,
    "order_items": RAW_ORDER_ITEMS_CSV,
    "products": RAW_PRODUCTS_CSV,
    "payments": RAW_ORDER_PAYMENTS_CSV,
    "reviews": RAW_ORDER_REVIEWS_CSV,
    "translations": RAW_TRANSLATIONS_CSV,
    RAW_CUSTOMERS_CSV: RAW_CUSTOMERS_CSV,
    RAW_ORDERS_CSV: RAW_ORDERS_CSV,
    RAW_ORDER_ITEMS_CSV: RAW_ORDER_ITEMS_CSV,
    RAW_PRODUCTS_CSV: RAW_PRODUCTS_CSV,
    RAW_ORDER_PAYMENTS_CSV: RAW_ORDER_PAYMENTS_CSV,
    RAW_ORDER_REVIEWS_CSV: RAW_ORDER_REVIEWS_CSV,
    RAW_TRANSLATIONS_CSV: RAW_TRANSLATIONS_CSV,
}


class CSVLoader:
    """
    Extracted data reader for raw CSV datasets stored in data/raw/.
    """

    def __init__(self, settings: Optional[ETLSettings] = None) -> None:
        """
        Initialize CSVLoader with configuration settings.

        Args:
            settings: ETL configuration instance. Defaults to application etl_settings.
        """
        self.settings = settings or etl_settings

    def _resolve_filename(self, target: Union[str, DatasetType]) -> str:
        """
        Resolve DatasetType enum or dataset key string to raw CSV filename.
        """
        key = target.value if isinstance(target, DatasetType) else str(target)
        return DATASET_FILENAME_MAP.get(key, key)

    def load_dataset(
        self, filename: Union[str, DatasetType], encoding: str = "utf-8"
    ) -> pd.DataFrame:
        """
        Load a single raw CSV dataset file by name or DatasetType from RAW_DATA_DIR.

        Args:
            filename: Name of the CSV file or DatasetType enum (e.g. DatasetType.CUSTOMERS or 'olist_customers_dataset.csv').
            encoding: Text encoding format. Defaults to 'utf-8'.

        Returns:
            Extracted raw dataset as a pandas DataFrame.

        Raises:
            ETLExtractionError: If the file does not exist, is invalid/empty, or missing required columns.
        """
        resolved_filename: str = self._resolve_filename(filename)
        file_path: Path = self.settings.RAW_DATA_DIR / resolved_filename
        logger.info(f"Initiating extraction for CSV dataset: '{resolved_filename}' from path: {file_path}")

        # Validate file existence
        if not file_path.exists():
            error_msg = f"Raw dataset file not found: {file_path.resolve()}"
            logger.error(error_msg)
            raise ETLExtractionError(message=error_msg, details=f"Filename: {resolved_filename}")

        if not file_path.is_file():
            error_msg = f"Target path is not a file: {file_path.resolve()}"
            logger.error(error_msg)
            raise ETLExtractionError(message=error_msg, details=f"Filename: {resolved_filename}")

        # Read CSV file
        try:
            df: pd.DataFrame = pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError as exc:
            logger.warning(f"UTF-8 decoding failed for '{resolved_filename}'. Attempting fallback with 'latin-1'...")
            try:
                df = pd.read_csv(file_path, encoding="latin-1")
            except Exception as fallback_exc:
                error_msg = f"Failed to parse CSV file '{resolved_filename}' with UTF-8 and fallback encodings."
                logger.error(f"{error_msg} Details: {str(fallback_exc)}")
                raise ETLExtractionError(message=error_msg, details=str(fallback_exc)) from fallback_exc
        except Exception as exc:
            error_msg = f"Unexpected error reading CSV file '{resolved_filename}': {str(exc)}"
            logger.error(error_msg)
            raise ETLExtractionError(message=error_msg, details=str(exc)) from exc

        # Check for empty dataframe
        if df.empty and file_path.stat().st_size > 0:
            error_msg = f"Extracted DataFrame for '{resolved_filename}' is empty despite non-zero file size."
            logger.warning(error_msg)

        # Validate required columns if configured
        if resolved_filename in REQUIRED_COLUMNS:
            expected_cols: List[str] = REQUIRED_COLUMNS[resolved_filename]
            missing_cols: List[str] = [col for col in expected_cols if col not in df.columns]
            if missing_cols:
                error_msg = (
                    f"Dataset '{resolved_filename}' is missing required columns: {missing_cols}. "
                    f"Expected: {expected_cols}, Found: {list(df.columns)}"
                )
                logger.error(error_msg)
                raise ETLExtractionError(message=error_msg, details=f"Missing: {missing_cols}")

        # Log loading statistics
        file_size_kb: float = file_path.stat().st_size / 1024.0
        memory_usage_mb: float = df.memory_usage(deep=True).sum() / (1024.0 * 1024.0)
        logger.info(
            f"Successfully loaded '{filename}' | "
            f"Rows: {len(df):,} | Columns: {len(df.columns)} | "
            f"File Size: {file_size_kb:.2f} KB | Memory: {memory_usage_mb:.2f} MB"
        )

        return df

    def detect_and_load(self, file_path: Path, encoding: str = "utf-8") -> pd.DataFrame:
        """
        Automatically detect dataset identity from a file path and load it.

        Args:
            file_path: Absolute or relative Path object to the target CSV file.
            encoding: Text encoding format. Defaults to 'utf-8'.

        Returns:
            Extracted raw dataset as a pandas DataFrame.

        Raises:
            ETLExtractionError: If file path is invalid or dataset extraction fails.
        """
        filename: str = file_path.name
        logger.info(f"Auto-detecting and loading dataset from path: {file_path}")
        return self.load_dataset(filename=filename, encoding=encoding)

    # -------------------------------------------------------------------------
    # Specialized Entity Loader Methods
    # -------------------------------------------------------------------------

    def load_customers(self) -> pd.DataFrame:
        """
        Extract the raw customers dataset (olist_customers_dataset.csv).

        Returns:
            Pandas DataFrame containing raw customer records.
        """
        return self.load_dataset(filename=RAW_CUSTOMERS_CSV)

    def load_orders(self) -> pd.DataFrame:
        """
        Extract the raw orders dataset (olist_orders_dataset.csv).

        Returns:
            Pandas DataFrame containing raw order header records.
        """
        return self.load_dataset(filename=RAW_ORDERS_CSV)

    def load_order_items(self) -> pd.DataFrame:
        """
        Extract the raw order line items dataset (olist_order_items_dataset.csv).

        Returns:
            Pandas DataFrame containing raw order item records.
        """
        return self.load_dataset(filename=RAW_ORDER_ITEMS_CSV)

    def load_products(self) -> pd.DataFrame:
        """
        Extract the raw products catalog dataset (olist_products_dataset.csv).

        Returns:
            Pandas DataFrame containing raw product records.
        """
        return self.load_dataset(filename=RAW_PRODUCTS_CSV)

    def load_payments(self) -> pd.DataFrame:
        """
        Extract the raw order payments dataset (olist_order_payments_dataset.csv).

        Returns:
            Pandas DataFrame containing raw payment records.
        """
        return self.load_dataset(filename=RAW_ORDER_PAYMENTS_CSV)

    def load_reviews(self) -> pd.DataFrame:
        """
        Extract the raw order reviews dataset (olist_order_reviews_dataset.csv).

        Returns:
            Pandas DataFrame containing raw customer review records.
        """
        return self.load_dataset(filename=RAW_ORDER_REVIEWS_CSV)

    def load_translations(self) -> pd.DataFrame:
        """
        Extract the raw product category translation dataset (product_category_name_translation.csv).

        Returns:
            Pandas DataFrame containing raw category translation mappings.
        """
        return self.load_dataset(filename=RAW_TRANSLATIONS_CSV)

    def load_all_raw_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Extract all configured raw CSV datasets from RAW_DATA_DIR.

        Returns:
            Dictionary mapping dataset filenames to extracted pandas DataFrames.
        """
        logger.info(f"Extracting all {len(RAW_DATASETS)} raw CSV datasets from: {self.settings.RAW_DATA_DIR}")
        datasets: Dict[str, pd.DataFrame] = {}
        for filename in RAW_DATASETS:
            datasets[filename] = self.load_dataset(filename=filename)

        logger.info(f"Successfully extracted all {len(datasets)} raw datasets.")
        return datasets
