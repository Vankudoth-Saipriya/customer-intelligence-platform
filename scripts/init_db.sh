#!/usr/bin/env bash
set -e

echo "Initializing Alembic migrations..."
alembic revision --autogenerate -m "Initial baseline migration"
alembic upgrade head
echo "Database migration complete."
