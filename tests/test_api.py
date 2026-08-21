"""
Integration tests for FastAPI REST API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_api_v1_models_info(async_client: AsyncClient):
    """
    Test GET /api/v1/ml/models endpoint returns catalog of trained models.
    """
    response = await async_client.get("/api/v1/ml/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert "customer_segmentation" in data["models"]


@pytest.mark.anyio
async def test_api_v1_segment_prediction(async_client: AsyncClient):
    """
    Test POST /api/v1/ml/segment endpoint.
    """
    payload = {
        "customer_id": "00012a2504309823e6e38064373a51d2",
        "recency_days": 100.0,
        "frequency_orders": 1,
        "monetary_value": 150.0
    }
    response = await async_client.post("/api/v1/ml/segment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "cluster_id" in data
    assert "business_description" in data


@pytest.mark.anyio
async def test_api_v1_clv_prediction(async_client: AsyncClient):
    """
    Test POST /api/v1/ml/clv endpoint.
    """
    payload = {
        "customer_id": "00012a2504309823e6e38064373a51d2",
        "recency_days": 100.0,
        "frequency_orders": 1,
        "monetary_value": 150.0
    }
    response = await async_client.post("/api/v1/ml/clv", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_clv" in data
    assert data["predicted_clv"] >= 0.0


@pytest.mark.anyio
async def test_api_v1_repeat_purchase_prediction(async_client: AsyncClient):
    """
    Test POST /api/v1/ml/repeat-purchase endpoint.
    """
    payload = {
        "customer_id": "00012a2504309823e6e38064373a51d2",
        "recency_days": 100.0,
        "frequency_orders": 1,
        "monetary_value": 150.0
    }
    response = await async_client.post("/api/v1/ml/repeat-purchase", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "repeat_purchase_probability" in data
    assert "predicted_repeat_customer" in data
