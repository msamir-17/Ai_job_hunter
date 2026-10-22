"""
Cross-Tenant Isolation Test.
Proves that User A cannot read or mutate User B's profile or applications.
"""
import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.database import engine
from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True)
async def dispose_db_engine():
    yield
    await engine.dispose()


@pytest.mark.anyio
async def test_cross_tenant_isolation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register User Alice
        alice_email = f"alice_{uuid.uuid4().hex[:8]}@example.com"
        alice_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": alice_email,
                "password": "Password123!",
                "full_name": "Alice Engineer",
            },
        )
        assert alice_reg.status_code == 201, alice_reg.text
        alice_data = alice_reg.json()
        alice_token = alice_data["access_token"]
        alice_id = alice_data["user"]["id"]
        alice_headers = {"Authorization": f"Bearer {alice_token}"}

        # 2. Register User Bob
        bob_email = f"bob_{uuid.uuid4().hex[:8]}@example.com"
        bob_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": bob_email,
                "password": "Password123!",
                "full_name": "Bob Analyst",
            },
        )
        assert bob_reg.status_code == 201, bob_reg.text
        bob_data = bob_reg.json()
        bob_token = bob_data["access_token"]
        bob_id = bob_data["user"]["id"]
        bob_headers = {"Authorization": f"Bearer {bob_token}"}

        # 3. Alice gets and updates her candidate profile
        alice_profile_res = await client.get("/api/v1/candidate-profile/me", headers=alice_headers)
        assert alice_profile_res.status_code == 200
        alice_profile = alice_profile_res.json()
        alice_profile_id = alice_profile["id"]

        alice_update = await client.put(
            "/api/v1/candidate-profile/me",
            headers=alice_headers,
            json={
                "headline": "Lead AI Architect",
                "summary": "Deep learning and vector databases specialist.",
                "skills": ["python", "pytorch", "pgvector"],
                "target_titles": ["Staff AI Engineer"],
            },
        )
        assert alice_update.status_code == 200
        assert alice_update.json()["headline"] == "Lead AI Architect"

        # 4. Bob attempts to access Alice's profile via candidate-profile ID -> 403 Forbidden!
        bob_snoop = await client.get(f"/api/v1/candidate-profile/{alice_profile_id}", headers=bob_headers)
        assert bob_snoop.status_code == 403
        assert "forbidden" in bob_snoop.json()["detail"].lower()

        # 5. Bob attempts to overwrite Alice's profile -> 403 Forbidden!
        bob_hack = await client.put(
            f"/api/v1/candidate-profile/{alice_profile_id}",
            headers=bob_headers,
            json={"headline": "Hacked Profile"},
        )
        assert bob_hack.status_code == 403

        # 6. Bob attempts to query Alice's applications -> 403 Forbidden!
        bob_app_query = await client.get(f"/api/v1/applications?user_id={alice_id}", headers=bob_headers)
        assert bob_app_query.status_code == 403

        # 7. Bob checks his own profile -> Should have Bob's identity, completely separated from Alice
        bob_profile_res = await client.get("/api/v1/candidate-profile/me", headers=bob_headers)
        assert bob_profile_res.status_code == 200
        bob_profile = bob_profile_res.json()
        assert bob_profile["id"] != alice_profile_id
        assert bob_profile["headline"] != "Lead AI Architect"
        assert bob_profile["email"] == bob_email

        # 8. Bob attempts to read Alice's job matches -> 403 Forbidden!
        bob_matches_snoop = await client.get(
            f"/api/v1/matching/candidate/{alice_profile_id}/matches",
            headers=bob_headers,
        )
        assert bob_matches_snoop.status_code == 403

        # 9. Bob attempts to trigger deterministic filtering on Alice's profile -> 403 Forbidden!
        bob_filter_hack = await client.post(
            "/api/v1/matching/deterministic/filter",
            headers=bob_headers,
            json={"candidate_profile_id": str(alice_profile_id)},
        )
        assert bob_filter_hack.status_code == 403

        # 10. Bob attempts to trigger tailoring on Alice's profile -> 403 Forbidden!
        bob_tailor_hack = await client.post(
            "/api/v1/tailoring/generate",
            headers=bob_headers,
            json={"candidate_profile_id": str(alice_profile_id), "job_id": str(uuid.uuid4())},
        )
        assert bob_tailor_hack.status_code == 403

