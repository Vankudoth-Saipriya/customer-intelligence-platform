"""
Custom exception hierarchy for ETL pipeline errors.
"""

from typing import Optional


class ETLException(Exception):
    """
    Base exception class for all ETL pipeline exceptions.
    """

    def __init__(self, message: str, details: Optional[str] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class ETLConfigurationError(ETLException):
    """
    Raised when ETL configuration parameters or environment paths are invalid.
    """

    pass


class ETLExtractionError(ETLException):
    """
    Raised when an error occurs during raw data reading or extraction.
    """

    pass


class ETLValidationError(ETLException):
    """
    Raised when dataset validation or schema checks fail.
    """

    pass


class ETLTransformationError(ETLException):
    """
    Raised when data transformation, cleaning, or derived calculation fails.
    """

    pass


class ETLLoadError(ETLException):
    """
    Raised when bulk loading or database insertion fails.
    """

    pass


class CircuitBreakerTriggeredError(ETLException):
    """
    Raised when error threshold percentage is exceeded, halting the pipeline.
    """

    pass
