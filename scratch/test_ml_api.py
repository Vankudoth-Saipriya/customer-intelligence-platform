"""
Unit tests for ML Inference API layer using FastAPI TestClient.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ml_health_endpoint():
    """
    Test GET /api/v1/ml/health
    """
    response = client.get("/api/v1/ml/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "inference_available" in data
    assert isinstance(data["loaded_models"], list)


def test_ml_models_info_endpoint():
    """
    Test GET /api/v1/ml/models
    """
    response = client.get("/api/v1/ml/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert isinstance(data["models"], dict)


def test_segment_prediction_endpoint():
    """
    Test POST /api/v1/ml/segment
    """
    payload = {
        "state": "SP",
        "city": "sao paulo",
        "recency_days": 15.0,
        "frequency_orders": 2,
        "monetary_value": 350.0,
        "avg_order_value": 175.0,
        "total_items": 3,
        "favorite_product_category": "health_beauty",
        "preferred_payment_method": "credit_card",
        "avg_review_score": 4.8,
        "total_revenue": 350.0,
        "customer_value_tier": "High Value",
    }
    response = client.post("/api/v1/ml/segment", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "cluster_id" in data
    assert "cluster_name" in data
    assert "business_description" in data
    assert isinstance(data["cluster_id"], int)


def test_clv_prediction_endpoint():
    """
    Test POST /api/v1/ml/clv
    """
    payload = {
        "state": "RJ",
        "avg_order_value": 250.0,
        "frequency_orders": 3,
        "total_items": 4,
        "preferred_payment_method": "credit_card",
        "avg_review_score": 4.5,
        "total_revenue": 750.0,
    }
    response = client.post("/api/v1/ml/clv", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_clv" in data
    assert isinstance(data["predicted_clv"], (int, float))
    assert data["predicted_clv"] >= 0.0


def test_repeat_purchase_prediction_endpoint():
    """
    Test POST /api/v1/ml/repeat-purchase
    """
    payload = {
        "frequency_orders": 2,
        "total_items": 3,
        "avg_order_value": 150.0,
        "avg_payment_value": 150.0,
        "preferred_payment_method": "credit_card",
        "customer_value_tier": "Medium Value",
    }
    response = client.post("/api/v1/ml/repeat-purchase", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "repeat_purchase_probability" in data
    assert "predicted_repeat_customer" in data
    assert 0.0 <= data["repeat_purchase_probability"] <= 1.0
    assert data["predicted_repeat_customer"] in [0, 1]


def test_invalid_payload_validation():
    """
    Test validation failure with invalid types (e.g. string for frequency_orders).
    """
    payload = {
        "frequency_orders": "invalid_integer_string_abc",
    }
    response = client.post("/api/v1/ml/segment", json=payload)
    assert response.status_code == 422


if __name__ == "__main__":
    test_ml_health_endpoint()
    test_ml_models_info_endpoint()
    test_segment_prediction_endpoint()
    test_clv_prediction_endpoint()
    test_repeat_purchase_prediction_endpoint()
    test_invalid_payload_validation()
    print("All ML API unit tests passed successfully!")
