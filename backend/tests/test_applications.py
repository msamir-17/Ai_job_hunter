import uuid
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from app.api.applications import map_application_to_response
from app.models import Application, GeneratedDocument, Job, JobMatch
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    GeneratedDocumentCreate,
    GeneratedDocumentUpdate,
)


def test_application_create_schema_valid_statuses():
    """Verify ApplicationCreate validates allowed status literals."""
    user_id = uuid.uuid4()
    match_id = uuid.uuid4()

    for valid_status in ["saved", "applied", "interviewing", "rejected", "offer"]:
        payload = ApplicationCreate(
            user_id=user_id,
            job_match_id=match_id,
            status=valid_status,
        )
        assert payload.status == valid_status

    # Invalid status should raise ValidationError
    with pytest.raises(ValidationError):
        ApplicationCreate(
            user_id=user_id,
            job_match_id=match_id,
            status="invalid_status",
        )


def test_generated_document_schema_validation():
    """Verify document schema validation for types and content."""
    doc = GeneratedDocumentCreate(
        doc_type="tailored_resume_bullets",
        content="Engineered high throughput pipelines.",
        is_approved_by_user=True,
    )
    assert doc.doc_type == "tailored_resume_bullets"
    assert doc.is_approved_by_user is True

    # Empty content should fail validation
    with pytest.raises(ValidationError):
        GeneratedDocumentCreate(
            doc_type="cover_letter",
            content="",
        )


def test_map_application_to_response_enrichment():
    """Verify map_application_to_response extracts job fields and document list."""
    job_id = uuid.uuid4()
    job = Job(
        id=job_id,
        title="MLOps Engineer",
        company="Vector Infrastructure",
        location="Remote",
        is_remote=True,
        url="https://example.com/apply",
    )
    match = JobMatch(
        id=uuid.uuid4(),
        job=job,
    )
    app_id = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    doc = GeneratedDocument(
        id=uuid.uuid4(),
        application_id=app_id,
        doc_type="cover_letter",
        content="Dear Team...",
        is_approved_by_user=False,
    )

    app_record = Application(
        id=app_id,
        user_id=user_id,
        job_match_id=match.id,
        job_match=match,
        status="applied",
        applied_at=now,
        notes="Applied via company portal",
        generated_documents=[doc],
    )

    response = map_application_to_response(app_record)

    assert response.id == app_id
    assert response.status == "applied"
    assert response.job_title == "MLOps Engineer"
    assert response.job_company == "Vector Infrastructure"
    assert response.job_is_remote is True
    assert response.job_url == "https://example.com/apply"
    assert len(response.documents) == 1
    assert response.documents[0].doc_type == "cover_letter"
    assert response.documents[0].is_approved_by_user is False
