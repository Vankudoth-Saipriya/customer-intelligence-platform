"""
ETL configuration management extending application core settings.
"""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config import settings as core_settings
from app.etl.utils.constants import (
    DEFAULT_BATCH_CHUNK_SIZE,
    DEFAULT_ERROR_THRESHOLD_PERCENT,
    DEFAULT_MAX_RETRIES,
)


class ETLSettings(BaseSettings):
    """
    Configuration settings for ETL extraction, transformation, and load pipelines.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    RAW_DATA_DIR: Path = Field(
        default=Path("data/raw"),
        description="Path to raw input CSV files directory.",
    )
    QUARANTINE_DIR: Path = Field(
        default=Path("data/quarantine"),
        description="Path to quarantine directory for malformed records.",
    )
    FEATURE_STORE_DIR: Path = Field(
        default=Path("data/feature_store"),
        description="Path to offline Parquet feature store directory.",
    )
    BATCH_CHUNK_SIZE: int = Field(
        default=DEFAULT_BATCH_CHUNK_SIZE,
        description="Chunk size for batch processing records.",
    )
    ERROR_THRESHOLD_PERCENT: float = Field(
        default=DEFAULT_ERROR_THRESHOLD_PERCENT,
        description="Error rate threshold percentage before triggering circuit breaker.",
    )
    MAX_RETRIES: int = Field(
        default=DEFAULT_MAX_RETRIES,
        description="Maximum retry attempts for transient DB load errors.",
    )
    DATABASE_URL: str = Field(
        default_factory=lambda: core_settings.ASYNC_DATABASE_URL,
        description="PostgreSQL async connection string.",
    )


etl_settings = ETLSettings()
