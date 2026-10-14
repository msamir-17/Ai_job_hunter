"""
Integration test suite for Authentication & User Account Management endpoints.
Tests register, login, me, and GDPR data deletion against real PostgreSQL (port 5435).
"""
import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal, engine
from app.main import app
from app.models import User


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_auth_registration_and_login_flow():
    """
    Test complete authentication lifecycle:
    1. Register new user -> 201 with JWT access token.
    2. Attempt duplicate registration -> 409 Conflict.
    3. Login with correct credentials -> 200 with JWT access token.
    4. Login with invalid password -> 401 Unauthorized.
    5. Access /auth/me with Bearer token -> 200 with user profile.
    6. Access /auth/me without token -> 401/403 Unauthorized.
    7. Delete account (/auth/me) -> 204 No Content.
    8. Verify user deleted from database.
    """
    test_id = uuid.uuid4().hex[:8]
    test_email = f"auth_test_{test_id}@example.com"
    test_password = "StrongPassword123!"
    test_name = "Auth Test Candidate"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register new user
        reg_payload = {
            "email": test_email,
            "password": test_password,
            "full_name": test_name,
        }
        res_reg = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_reg.status_code == 201, f"Registration failed: {res_reg.text}"
        reg_data = res_reg.json()
        assert "access_token" in reg_data
        assert reg_data["user"]["email"] == test_email
        token = reg_data["access_token"]

        # 2. Duplicate registration attempt
        res_dup = await client.post("/api/v1/auth/register", json=reg_payload)
        assert res_dup.status_code == 409
        assert "already exists" in res_dup.json()["detail"]

        # 3. Login with correct password
        login_payload = {
            "email": test_email,
            "password": test_password,
        }
        res_login = await client.post("/api/v1/auth/login", json=login_payload)
        assert res_login.status_code == 200
        login_data = res_login.json()
        assert "access_token" in login_data
        assert login_data["user"]["email"] == test_email

        # 4. Login with wrong password
        res_bad_login = await client.post("/api/v1/auth/login", json={
            "email": test_email,
            "password": "WrongPassword!",
        })
        assert res_bad_login.status_code == 401

        # 5. Access /auth/me with Bearer token
        headers = {"Authorization": f"Bearer {token}"}
        res_me = await client.get("/api/v1/auth/me", headers=headers)
        assert res_me.status_code == 200
        me_data = res_me.json()
        assert me_data["email"] == test_email
        assert me_data["full_name"] == test_name

        # 6. Access /auth/me without token -> rejected
        res_unauth = await client.get("/api/v1/auth/me")
        assert res_unauth.status_code in {401, 403}

        # 7. Delete account (/auth/me) -> GDPR cascade deletion
        res_del = await client.delete("/api/v1/auth/me", headers=headers)
        assert res_del.status_code == 204

        # 8. Verify user is removed from PostgreSQL
        async with AsyncSessionLocal() as db:
            stmt = select(User).where(User.email == test_email)
            u = (await db.execute(stmt)).scalar_one_or_none()
            assert u is None, "User was not deleted from database!"
