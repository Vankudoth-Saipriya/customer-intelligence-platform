#!/bin/sh
set -e

if [ -n "${POSTGRES_SERVER}" ] && [ "${POSTGRES_SERVER}" != "none" ]; then
  echo "Waiting for PostgreSQL database at ${POSTGRES_SERVER}:${POSTGRES_PORT:-5432}..."
  count=0
  max_retries=10
  while ! nc -z "${POSTGRES_SERVER}" "${POSTGRES_PORT:-5432}"; do
    count=$((count + 1))
    if [ "$count" -ge "$max_retries" ]; then
      echo "Warning: PostgreSQL database not reachable after $max_retries attempts. Continuing with local artifacts..."
      break
    fi
    sleep 0.5
  done
  if [ "$count" -lt "$max_retries" ]; then
    echo "PostgreSQL is up and running!"
    echo "Running database migrations..."
    alembic upgrade head || echo "Alembic migration step finished."
  fi
else
  echo "No PostgreSQL server configured. Running in standalone artifact mode."
fi

echo "Starting application server..."
exec "$@"
