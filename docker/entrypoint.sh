#!/bin/sh
set -e

echo "Waiting for PostgreSQL database at ${POSTGRES_SERVER}:${POSTGRES_PORT}..."
while ! nc -z "${POSTGRES_SERVER}" "${POSTGRES_PORT}"; do
  sleep 0.5
done
echo "PostgreSQL is up and running!"

echo "Running database migrations..."
alembic upgrade head

echo "Starting application server..."
exec "$@"
