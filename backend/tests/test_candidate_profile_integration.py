import uuid
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.main import app
from app.models import CandidateProfile, User


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_candidate_profile_crud_real_db():
    """
    Integration test verifying Candidate Profile CRUD endpoints against
    the real Docker PostgreSQL + pgvector database on port 5435.
    """
    test_user_id = uuid.uuid4()
    test_email = f"integration_test_{test_user_id.hex[:8]}@example.com"
    created_profile_id = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        try:
            # 1. Create a test User directly in the real PostgreSQL database (port 5435)
            async with AsyncSessionLocal() as db:
                test_user = User(
                    id=test_user_id,
                    email=test_email,
                    hashed_password="hashed_integration_password",
                    full_name="Integration Test Candidate",
                )
                db.add(test_user)
                await db.commit()

            # 2. CREATE CandidateProfile via real FastAPI endpoint
            create_payload = {
                "user_id": str(test_user_id),
                "headline": "Real DB Integration Candidate",
                "summary": "Testing CRUD operations against Docker pgvector database.",
                "skills": ["Python", "FastAPI", "PostgreSQL", "pgvector"],
                "experience": [{"company": "Test Co", "role": "QA Engineer", "years": 2}],
                "education": [{"degree": "B.S. Software Engineering", "school": "Test University"}],
                "target_titles": ["Senior QA Engineer", "Backend Developer"],
            }

            response = await async_client.post("/api/v1/candidate-profile", json=create_payload)
            assert response.status_code == 201, f"Create failed: {response.text}"
            data = response.json()
            assert data["user_id"] == str(test_user_id)
            assert data["headline"] == "Real DB Integration Candidate"
            assert "pgvector" in data["skills"]
            created_profile_id = data["id"]

            # 3. READ CandidateProfile via real GET endpoint
            get_response = await async_client.get(f"/api/v1/candidate-profile/{created_profile_id}")
            assert get_response.status_code == 200, f"Get failed: {get_response.text}"
            get_data = get_response.json()
            assert get_data["id"] == created_profile_id
            assert get_data["headline"] == "Real DB Integration Candidate"

            # 4. UPDATE CandidateProfile via real PUT endpoint
            update_payload = {
                "headline": "Lead Integration Engineer",
                "skills": ["Python", "FastAPI", "PostgreSQL", "pgvector", "Docker"],
            }
            put_response = await async_client.put(
                f"/api/v1/candidate-profile/{created_profile_id}", json=update_payload
            )
            assert put_response.status_code == 200, f"Update failed: {put_response.text}"
            put_data = put_response.json()
            assert put_data["headline"] == "Lead Integration Engineer"
            assert "Docker" in put_data["skills"]

            # Verify update persisted in GET
            get_after_put = await async_client.get(f"/api/v1/candidate-profile/{created_profile_id}")
            assert get_after_put.status_code == 200
            assert get_after_put.json()["headline"] == "Lead Integration Engineer"

            # 5. DELETE CandidateProfile via real DELETE endpoint
            delete_response = await async_client.delete(f"/api/v1/candidate-profile/{created_profile_id}")
            assert delete_response.status_code == 204

            # Verify profile is deleted (404)
            get_after_delete = await async_client.get(f"/api/v1/candidate-profile/{created_profile_id}")
            assert get_after_delete.status_code == 404

        finally:
            # 6. Clean up test records from real PostgreSQL database
            async with AsyncSessionLocal() as db:
                if created_profile_id:
                    await db.execute(
                        delete(CandidateProfile).where(
                            CandidateProfile.id == uuid.UUID(created_profile_id)
                        )
                    )
                await db.execute(delete(User).where(User.id == test_user_id))
                await db.commit()
