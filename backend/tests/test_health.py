import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    """Test that /health returns HTTP 200 and expected status object."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "AI Job Hunter Co-Pilot API"
    assert "environment" in data
    assert "active_llm_provider" in data
