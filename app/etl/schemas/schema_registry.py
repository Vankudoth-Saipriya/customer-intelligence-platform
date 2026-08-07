"""
Central Schema Registry for dataset schema management and lookup.
"""

from typing import Dict, List, Union
from loguru import logger

from app.etl.schemas.base_schema import DatasetSchema
from app.etl.schemas.customers_schema import CUSTOMERS_SCHEMA
from app.etl.schemas.order_items_schema import ORDER_ITEMS_SCHEMA
from app.etl.schemas.orders_schema import ORDERS_SCHEMA
from app.etl.schemas.payments_schema import PAYMENTS_SCHEMA
from app.etl.schemas.products_schema import PRODUCTS_SCHEMA
from app.etl.schemas.reviews_schema import REVIEWS_SCHEMA
from app.etl.schemas.translations_schema import TRANSLATIONS_SCHEMA
from app.etl.utils.dataset_types import DatasetType
from app.etl.utils.exceptions import ETLConfigurationError


class SchemaRegistry:
    """
    Registry managing dataset schema definitions for consuming validators.
    """

    def __init__(self) -> None:
        """
        Initialize the registry and register default dataset schemas.
        """
        self._registry: Dict[str, DatasetSchema] = {}
        self._register_defaults()

    def _resolve_name(self, dataset_name: Union[str, DatasetType]) -> str:
        """
        Resolve dataset_name parameter to string key.
        """
        if isinstance(dataset_name, DatasetType):
            return dataset_name.value
        return str(dataset_name)

    def _register_defaults(self) -> None:
        """
        Register standard dataset schemas.
        """
        self.register(CUSTOMERS_SCHEMA)
        self.register(ORDERS_SCHEMA)
        self.register(ORDER_ITEMS_SCHEMA)
        self.register(PRODUCTS_SCHEMA)
        self.register(PAYMENTS_SCHEMA)
        self.register(REVIEWS_SCHEMA)
        self.register(TRANSLATIONS_SCHEMA)

    def register(self, schema: DatasetSchema) -> None:
        """
        Register a DatasetSchema instance.

        Args:
            schema: DatasetSchema instance to register.

        Raises:
            ETLConfigurationError: If schema has an empty name.
        """
        if not schema.name:
            raise ETLConfigurationError("Cannot register a schema with an empty name.")

        self._registry[schema.name] = schema
        logger.debug(f"Registered schema for dataset: '{schema.name}'")

    def get(self, dataset_name: Union[str, DatasetType]) -> DatasetSchema:
        """
        Retrieve a registered DatasetSchema by dataset name or DatasetType.

        Args:
            dataset_name: Name or DatasetType enum of the dataset schema to retrieve.

        Returns:
            The registered DatasetSchema instance.

        Raises:
            ETLConfigurationError: If dataset_name is not registered.
        """
        name_key = self._resolve_name(dataset_name)
        if not self.exists(name_key):
            error_msg = f"Schema not found for dataset: '{name_key}'."
            logger.error(error_msg)
            raise ETLConfigurationError(
                message=error_msg,
                details=f"Available schemas: {self.list_datasets()}",
            )
        return self._registry[name_key]

    def exists(self, dataset_name: Union[str, DatasetType]) -> bool:
        """
        Check if a dataset schema is registered.

        Args:
            dataset_name: Name or DatasetType enum of the dataset schema to check.

        Returns:
            True if registered, False otherwise.
        """
        name_key = self._resolve_name(dataset_name)
        return name_key in self._registry

    def list_datasets(self) -> List[str]:
        """
        List all registered dataset schema names.

        Returns:
            Sorted list of registered dataset schema names.
        """
        return sorted(list(self._registry.keys()))

    def all(self) -> Dict[str, DatasetSchema]:
        """
        Retrieve a copy of all registered schemas mapping dataset names to DatasetSchema objects.

        Returns:
            Dictionary of dataset names to DatasetSchema objects.
        """
        return dict(self._registry)


# Singleton instance export
schema_registry = SchemaRegistry()
