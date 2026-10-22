import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_llm_provider_info():
    """Verify GET /api/v1/settings/llm-provider returns active provider and policy disclosure."""
    response = client.get("/api/v1/settings/llm-provider")
    assert response.status_code == 200
    data = response.json()

    assert "active_provider" in data
    assert "display_name" in data
    assert "policy_url" in data
    assert "privacy_notice" in data
    assert data["is_third_party"] is True
    assert data["policy_url"].startswith("http")
