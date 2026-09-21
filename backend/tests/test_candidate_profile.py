import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.models import CandidateProfile, User

client = TestClient(app)


# Sample UUIDs for testing
TEST_USER_ID = uuid.uuid4()
TEST_PROFILE_ID = uuid.uuid4()


@pytest.fixture
def mock_db():
    """Mock AsyncSession for FastAPI dependency override."""
    session = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_user():
    user = User(
        id=TEST_USER_ID,
        email="testuser@example.com",
        hashed_password="hashedpassword123",
        full_name="Test Candidate",
    )
    return user


@pytest.fixture
def sample_profile(sample_user):
    profile = CandidateProfile(
        id=TEST_PROFILE_ID,
        user_id=sample_user.id,
        headline="AI Engineer",
        summary="Passionate about machine learning and NLP.",
        skills=["Python", "FastAPI", "PyTorch"],
        experience=[
            {"company": "Tech Corp", "role": "ML Intern", "years": 1}
        ],
        education=[{"degree": "B.S. Computer Science", "school": "Tech Uni"}],
        target_titles=["AI Engineer", "ML Engineer"],
    )
    return profile


class TestCreateCandidateProfile:
    def test_create_profile_success(self, mock_db, sample_user):
        # 1st execute: User check (found user)
        # 2nd execute: Existing profile check (no existing profile)
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = sample_user

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_user_result, mock_existing_result]

        app.dependency_overrides[get_db] = lambda: mock_db

        payload = {
            "user_id": str(TEST_USER_ID),
            "headline": "Fresh AI Graduate",
            "summary": "Building modern AI systems",
            "skills": ["Python", "SQLAlchemy"],
            "experience": [],
            "education": [],
            "target_titles": ["AI Engineer"],
        }

        response = client.post("/api/v1/candidate-profile", json=payload)
        app.dependency_overrides.clear()

        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(TEST_USER_ID)
        assert data["headline"] == "Fresh AI Graduate"
        assert data["skills"] == ["Python", "SQLAlchemy"]

    def test_create_profile_nonexistent_user(self, mock_db):
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = None

        mock_db.execute.return_value = mock_user_result
        app.dependency_overrides[get_db] = lambda: mock_db

        non_existent_user_id = uuid.uuid4()
        payload = {
            "user_id": str(non_existent_user_id),
            "headline": "AI Developer",
        }

        response = client.post("/api/v1/candidate-profile", json=payload)
        app.dependency_overrides.clear()

        assert response.status_code == 400
        assert f"User with id '{non_existent_user_id}' does not exist" in response.json()["detail"]

    def test_create_profile_duplicate_for_user(self, mock_db, sample_user, sample_profile):
        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = sample_user

        mock_existing_result = MagicMock()
        mock_existing_result.scalar_one_or_none.return_value = sample_profile

        mock_db.execute.side_effect = [mock_user_result, mock_existing_result]
        app.dependency_overrides[get_db] = lambda: mock_db

        payload = {
            "user_id": str(TEST_USER_ID),
            "headline": "Duplicate Profile",
        }

        response = client.post("/api/v1/candidate-profile", json=payload)
        app.dependency_overrides.clear()

        assert response.status_code == 409
        assert f"Candidate profile already exists for user '{TEST_USER_ID}'" in response.json()["detail"]


class TestGetCandidateProfile:
    def test_get_profile_success(self, mock_db, sample_profile):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_profile
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.get(f"/api/v1/candidate-profile/{TEST_PROFILE_ID}")
        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(TEST_PROFILE_ID)
        assert data["user_id"] == str(TEST_USER_ID)
        assert data["headline"] == "AI Engineer"

    def test_get_profile_not_found(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_db] = lambda: mock_db

        random_id = uuid.uuid4()
        response = client.get(f"/api/v1/candidate-profile/{random_id}")
        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Candidate profile not found."


class TestUpdateCandidateProfile:
    def test_update_profile_success(self, mock_db, sample_profile):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_profile
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_db] = lambda: mock_db

        payload = {
            "headline": "Senior AI Engineer",
            "skills": ["Python", "FastAPI", "PyTorch", "pgvector"],
        }

        response = client.put(f"/api/v1/candidate-profile/{TEST_PROFILE_ID}", json=payload)
        app.dependency_overrides.clear()

        assert response.status_code == 200
        data = response.json()
        assert data["headline"] == "Senior AI Engineer"
        assert "pgvector" in data["skills"]

    def test_update_profile_not_found(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_db] = lambda: mock_db

        random_id = uuid.uuid4()
        payload = {"headline": "Updated Title"}

        response = client.put(f"/api/v1/candidate-profile/{random_id}", json=payload)
        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Candidate profile not found."


class TestDeleteCandidateProfile:
    def test_delete_profile_success(self, mock_db, sample_profile):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_profile
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_db] = lambda: mock_db

        response = client.delete(f"/api/v1/candidate-profile/{TEST_PROFILE_ID}")
        app.dependency_overrides.clear()

        assert response.status_code == 204
        assert mock_db.delete.called
        assert mock_db.commit.called

    def test_delete_profile_not_found(self, mock_db):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        app.dependency_overrides[get_db] = lambda: mock_db

        random_id = uuid.uuid4()
        response = client.delete(f"/api/v1/candidate-profile/{random_id}")
        app.dependency_overrides.clear()

        assert response.status_code == 404
        assert response.json()["detail"] == "Candidate profile not found."
