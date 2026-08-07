# Customer Intelligence Platform - Backend

Production-ready FastAPI backend for the Customer Intelligence Platform, built with Python 3.12, Clean Architecture, PostgreSQL, SQLAlchemy 2.0, Alembic, Loguru, Pytest, and Docker.

---

## Technical Stack

- **Python**: 3.12
- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Database**: PostgreSQL 16
- **ORM**: SQLAlchemy 2.0 (Async with `asyncpg`)
- **Migrations**: Alembic
- **Settings & Config**: Pydantic Settings
- **Logging**: Loguru
- **Testing**: Pytest & HTTPX
- **Containerization**: Docker & Docker Compose
- **CI/CD**: GitHub Actions

---

## Directory Structure

```text
app/
├── api/          # API route handlers & versioning (/api/v1)
├── core/         # Settings (config.py) and Logging (logging.py)
├── db/           # SQLAlchemy 2.0 async sessions & base models
├── models/       # Database ORM models
├── repositories/ # Data access abstraction
├── schemas/      # Pydantic data schemas
├── services/     # Business logic services
├── ml/           # Machine learning modules & models
├── utils/        # Utility helpers
└── main.py       # FastAPI application entry point

alembic/          # Database migration configurations & scripts
docs/             # Architectural & API documentation
docker/           # Docker setup scripts and configurations
scripts/          # Database and development helper scripts
tests/            # Automated test suite
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)

### Running with Docker Compose

1. Start the database and API services:
   ```bash
   docker compose up --build
   ```

2. Verify the health check endpoint:
   ```bash
   curl http://localhost:8000/health
   ```
   **Expected Response:**
   ```json
   {
       "status": "healthy"
   }
   ```

3. Interactive API documentation will be available at:
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Local Development (Without Docker)

1. Create and activate a Python 3.12 virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure `.env` file:
   ```bash
   cp .env.example .env
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## Running Tests

Execute pytest:
```bash
pytest tests/
```
