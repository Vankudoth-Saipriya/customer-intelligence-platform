# Render Production Deployment Guide

This guide details step-by-step instructions for deploying the **Customer Intelligence Platform (CIP)** to [Render](https://render.com) using either **Render Blueprints (`render.yaml`)** or **Docker Containers**.

---

## 🏗️ Deployment Architecture Overview

On Render, the Customer Intelligence Platform runs as two web services:
1. **`customer-intelligence-api`**: FastAPI application serving REST endpoints (`/api/v1/*`), health checks (`/health`), and OpenAPI Swagger UI (`/docs`).
2. **`customer-intelligence-dashboard`**: Interactive Streamlit web application on port `$PORT`.

```
                    ┌────────────────────────┐
                    │    GitHub Repository   │
                    └───────────┬────────────┘
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
   ┌───────────────────────────┐ ┌───────────────────────────┐
   │   FastAPI Web Service     │ │  Streamlit Web Service    │
   │ (customer-intelligence-api)│ │(customer-intelligence-dash)│
   │   Port: $PORT             │ │   Port: $PORT             │
   │   Health: /health         │ │   Headless Mode           │
   └───────────────────────────┘ └───────────────────────────┘
```

---

## Option 1: Deploying via Render Blueprint (`render.yaml`) — Recommended

Render Blueprints allow Infrastructure as Code (IaC) deployment directly from the repository's `render.yaml`.

### Step 1: Connect Repository to Render
1. Log in to [Render Dashboard](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Blueprints**.
3. Connect your GitHub repository: `customer-intelligence-platform`.
4. Render will detect `render.yaml` and parse both services:
   - `customer-intelligence-api`
   - `customer-intelligence-dashboard`

### Step 2: Configure Environment Variables
Verify environment variables in the Render Dashboard:

| Variable | Value | Service | Description |
| :--- | :---: | :---: | :--- |
| `ENVIRONMENT` | `production` | Both | Set production mode |
| `DEBUG` | `false` | API | Disable debug logging |
| `LOG_LEVEL` | `INFO` | API | Log verbosity level |
| `PYTHONUNBUFFERED` | `1` | Both | Direct log output |

### Step 3: Deploy Blueprint
Click **Apply Blueprint**. Render will build and deploy both services automatically.

---

## Option 2: Deploying via Docker Container

Render supports direct Docker deployments using the repository's `Dockerfile`.

### Step 1: Create Web Service from Dockerfile
1. On Render Dashboard, click **New +** $\rightarrow$ **Web Service**.
2. Select repository `customer-intelligence-platform`.
3. Set **Runtime**: `Docker`.
4. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set **Health Check Path**: `/health`

---

## 💾 Handling SQLite Databases & Artifacts on Render

The platform stores EDA JSON reports, Customer Feature Store Parquet tables, and trained ML `.joblib` pipelines under `artifacts/`.

- **Ephemeral File System Note**: Free Render instances restart periodically and reset non-committed disk files.
- **Production Artifact Protection**:
  1. All pre-generated artifacts (`artifacts/eda/`, `artifacts/features/`, `artifacts/ml/`) are committed directly to the repository so services start instantly with zero training overhead.
  2. For dynamic SQLite data updates, attach a **Render Persistent Disk** mounted at `/app/data` if required.

---

## 🧪 Post-Deployment Verification

Once deployed, verify operational health:

1. **Health Check Endpoint**:
   ```bash
   curl -i https://customer-intelligence-api.onrender.com/health
   ```
   *Expected Response*: `HTTP/1.1 200 OK` $\rightarrow$ `{"status": "healthy"}`

2. **OpenAPI Swagger Interactive Documentation**:
   Navigate to: `https://customer-intelligence-api.onrender.com/docs`

3. **ML Inference API Test**:
   ```bash
   curl -X POST "https://customer-intelligence-api.onrender.com/api/v1/ml/segment" \
        -H "Content-Type: application/json" \
        -d '{"customer_id": "00012a2504309823e6e38064373a51d2"}'
   ```

4. **Streamlit Web Dashboard**:
   Navigate to: `https://customer-intelligence-dashboard.onrender.com`
