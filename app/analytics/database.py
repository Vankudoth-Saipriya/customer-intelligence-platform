"""
Read-only database session and connection helpers for analytics.
"""

from typing import Generator
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def get_analytics_engine() -> Engine:
    """
    Create and return a SQLAlchemy Engine for analytical read-only operations.
    """
    db_url = settings.DATABASE_URL
    if not db_url:
        # Fallback to sync PostgreSQL driver or settings
        db_url = (
            f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
            f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        )
    logger.debug(f"Creating analytics database engine for: {db_url}")
    return create_engine(db_url, echo=False, pool_pre_ping=True)


def get_read_only_session(engine: Engine = None) -> Generator[Session, None, None]:
    """
    Provide a read-only transactional SQLAlchemy Session generator for analytical queries.
    """
    target_engine = engine or get_analytics_engine()
    SessionLocal = sessionmaker(bind=target_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
