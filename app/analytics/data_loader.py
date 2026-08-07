"""
Analytics Data Loader for reading domain tables into pandas DataFrames.
"""

from typing import Optional
from loguru import logger
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.database import get_analytics_engine
from app.analytics.sql_repository import SQLRepository


class AnalyticsDataLoader:
    """
    DataLoader fetching analytical DataFrames from PostgreSQL database.
    """

    def __init__(self, session: Optional[Session] = None) -> None:
        """
        Initialize AnalyticsDataLoader with optional Session.
        """
        self.session = session

    def _execute_to_df(self, query) -> pd.DataFrame:
        """
        Execute query and convert results into pandas DataFrame.
        """
        if self.session:
            return pd.read_sql_query(query, self.session.bind)
        else:
            engine = get_analytics_engine()
            with engine.connect() as conn:
                return pd.read_sql_query(query, conn)

    def load_customers(self) -> pd.DataFrame:
        """
        Load customers dataset as pandas DataFrame.
        """
        logger.info("Loading customers dataset for analytics...")
        query = SQLRepository.query_customers()
        df = self._execute_to_df(query)
        logger.info(f"Loaded customers dataset ({len(df):,} rows).")
        return df

    def load_orders(self) -> pd.DataFrame:
        """
        Load orders dataset as pandas DataFrame.
        """
        logger.info("Loading orders dataset for analytics...")
        query = SQLRepository.query_orders()
        df = self._execute_to_df(query)
        logger.info(f"Loaded orders dataset ({len(df):,} rows).")
        return df

    def load_products(self) -> pd.DataFrame:
        """
        Load products dataset as pandas DataFrame.
        """
        logger.info("Loading products dataset for analytics...")
        query = SQLRepository.query_products()
        df = self._execute_to_df(query)
        logger.info(f"Loaded products dataset ({len(df):,} rows).")
        return df

    def load_payments(self) -> pd.DataFrame:
        """
        Load payments dataset as pandas DataFrame.
        """
        logger.info("Loading payments dataset for analytics...")
        query = SQLRepository.query_payments()
        df = self._execute_to_df(query)
        logger.info(f"Loaded payments dataset ({len(df):,} rows).")
        return df

    def load_reviews(self) -> pd.DataFrame:
        """
        Load reviews dataset as pandas DataFrame.
        """
        logger.info("Loading reviews dataset for analytics...")
        query = SQLRepository.query_reviews()
        df = self._execute_to_df(query)
        logger.info(f"Loaded reviews dataset ({len(df):,} rows).")
        return df

    def load_order_items(self) -> pd.DataFrame:
        """
        Load order_items dataset as pandas DataFrame.
        """
        logger.info("Loading order_items dataset for analytics...")
        query = SQLRepository.query_order_items()
        df = self._execute_to_df(query)
        logger.info(f"Loaded order_items dataset ({len(df):,} rows).")
        return df

    def load_full_dataset(self) -> pd.DataFrame:
        """
        Load full joined analytical dataset as pandas DataFrame.
        """
        logger.info("Loading full joined analytical dataset...")
        query = SQLRepository.query_full_dataset()
        df = self._execute_to_df(query)
        logger.info(f"Loaded full analytical dataset ({len(df):,} rows).")
        return df
