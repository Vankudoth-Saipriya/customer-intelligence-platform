# Customer Intelligence Platform Architecture

## Overview
This platform follows Clean Architecture principles, ensuring modularity, testability, and decoupling between core layers:

- **api**: FastAPI route definitions, request/response lifecycle handlers, and API versioning (`/api/v1`).
- **core**: Configuration management via Pydantic Settings, global logging via Loguru.
- **db**: SQLAlchemy 2.0 Async database engines, session management, and base models.
- **models**: ORM domain entity models.
- **repositories**: Data access abstraction layer for database operations.
- **schemas**: Pydantic models for data validation, serialization, and API contracts.
- **services**: Domain logic and business rules layer.
- **ml**: Placeholder module for machine learning models, inference pipelines, and feature engineering.
- **utils**: Shared helper functions and utility routines.

## Database & Migrations
- **Engine**: Async SQLAlchemy 2.0 with `asyncpg` driver.
- **Migrations**: Alembic with async migration support (`env.py`).
