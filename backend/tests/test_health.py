import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    """Test that /health returns HTTP 200 and minimal operational status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_admin_health_check_unauthenticated():
    """Test that /api/v1/admin/health rejects requests without bearer token."""
    response = client.get("/api/v1/admin/health")
    assert response.status_code == 401

