"""
Logging utilities and Loguru context managers for ETL pipeline stages.
"""

from contextlib import contextmanager
import time
from typing import Any, Dict, Generator, Optional
from loguru import logger


def setup_etl_logger() -> None:
    """
    Initialize and bind Loguru logger for ETL pipeline operations.
    """
    logger.info("Initializing Loguru ETL logger context...")


@contextmanager
def log_stage_execution(
    stage_name: str, dataset_name: Optional[str] = None
) -> Generator[Dict[str, Any], None, None]:
    """
    Context manager to log and time ETL stage execution.

    Args:
        stage_name: Name of the ETL pipeline stage (e.g., 'EXTRACT', 'TRANSFORM').
        dataset_name: Optional target dataset or table name.

    Yields:
        Dictionary context for capturing metric metadata.
    """
    target = f" [{dataset_name}]" if dataset_name else ""
    logger.info(f"Starting stage: {stage_name}{target}")
    start_time = time.perf_counter()
    metrics: Dict[str, Any] = {"rows_processed": 0, "errors_encountered": 0}

    try:
        yield metrics
        elapsed_sec = time.perf_counter() - start_time
        logger.info(
            f"Completed stage: {stage_name}{target} in {elapsed_sec:.3f}s | "
            f"Rows: {metrics.get('rows_processed', 0)} | "
            f"Errors: {metrics.get('errors_encountered', 0)}"
        )
    except Exception as exc:
        elapsed_sec = time.perf_counter() - start_time
        logger.error(
            f"Failed stage: {stage_name}{target} after {elapsed_sec:.3f}s | Error: {str(exc)}"
        )
        raise
