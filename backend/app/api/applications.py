from datetime import datetime, timezone
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Application, GeneratedDocument, JobMatch, User
from app.schemas.application import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    GeneratedDocumentCreate,
    GeneratedDocumentResponse,
    GeneratedDocumentUpdate,
)

router = APIRouter(prefix="/api/v1/applications", tags=["Applications & Tracking"])


def map_application_to_response(app_record: Application) -> ApplicationResponse:
    """Helper to convert Application ORM model to enriched ApplicationResponse."""
    job = app_record.job_match.job if (app_record.job_match and app_record.job_match.job) else None

    return ApplicationResponse(
        id=app_record.id,
        user_id=app_record.user_id,
        job_match_id=app_record.job_match_id,
        status=app_record.status,
        applied_at=app_record.applied_at,
        notes=app_record.notes,
        job_id=job.id if job else None,
        job_title=job.title if job else None,
        job_company=job.company if job else None,
        job_location=job.location if job else None,
        job_is_remote=bool(job.is_remote) if (job and job.is_remote is not None) else False,
        job_url=job.url if job else None,
        documents=[
            GeneratedDocumentResponse.model_validate(doc)
            for doc in (app_record.generated_documents or [])
        ],
    )


@router.post(
    "",
    response_model=ApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job application",
    description="Creates a tracked application from a JobMatch, defaulting to 'saved' status.",
)
async def create_application(
    payload: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    # 1. Verify User exists
    res_user = await db.execute(select(User).where(User.id == payload.user_id))
    if not res_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{payload.user_id}' not found.",
        )

    # 2. Verify JobMatch exists
    res_match = await db.execute(
        select(JobMatch).options(selectinload(JobMatch.job)).where(JobMatch.id == payload.job_match_id)
    )
    job_match = res_match.scalar_one_or_none()
    if not job_match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"JobMatch with ID '{payload.job_match_id}' not found.",
        )

    # Auto-stamp applied_at if status is 'applied' and timestamp not provided
    applied_time = payload.applied_at
    if payload.status == "applied" and applied_time is None:
        applied_time = datetime.now(timezone.utc)

    new_app = Application(
        id=uuid.uuid4(),
        user_id=payload.user_id,
        job_match_id=payload.job_match_id,
        status=payload.status,
        applied_at=applied_time,
        notes=payload.notes,
    )
    db.add(new_app)
    await db.commit()
    await db.refresh(new_app)

    # Reload with relationships
    stmt = (
        select(Application)
        .options(
            selectinload(Application.job_match).selectinload(JobMatch.job),
            selectinload(Application.generated_documents),
        )
        .where(Application.id == new_app.id)
    )
    reloaded = (await db.execute(stmt)).scalar_one()
    return map_application_to_response(reloaded)


@router.get(
    "",
    response_model=list[ApplicationResponse],
    status_code=status.HTTP_200_OK,
    summary="List applications with optional status/user filtering",
    description="Retrieves a list of tracked applications. Filter by status to query Kanban board columns.",
)
async def list_applications(
    user_id: UUID | None = Query(default=None, description="Filter by user UUID"),
    app_status: str | None = Query(default=None, alias="status", description="Filter by status: 'saved', 'applied', etc."),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[ApplicationResponse]:
    stmt = select(Application).options(
        selectinload(Application.job_match).selectinload(JobMatch.job),
        selectinload(Application.generated_documents),
    )

    if user_id:
        stmt = stmt.where(Application.user_id == user_id)
    if app_status:
        stmt = stmt.where(Application.status == app_status.strip().lower())

    stmt = stmt.order_by(Application.id.desc()).offset(offset).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [map_application_to_response(app_rec) for app_rec in rows]


@router.get(
    "/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get application details",
    description="Retrieves an application record with attached documents and job details.",
)
async def get_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    stmt = (
        select(Application)
        .options(
            selectinload(Application.job_match).selectinload(JobMatch.job),
            selectinload(Application.generated_documents),
        )
        .where(Application.id == application_id)
    )
    app_rec = (await db.execute(stmt)).scalar_one_or_none()
    if not app_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{application_id}' not found.",
        )
    return map_application_to_response(app_rec)


@router.patch(
    "/{application_id}",
    response_model=ApplicationResponse,
    status_code=status.HTTP_200_OK,
    summary="Update application status or notes",
    description="Moves an application across Kanban columns ('saved' -> 'applied' -> 'interviewing' -> 'offer'/'rejected').",
)
async def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
) -> ApplicationResponse:
    stmt = (
        select(Application)
        .options(
            selectinload(Application.job_match).selectinload(JobMatch.job),
            selectinload(Application.generated_documents),
        )
        .where(Application.id == application_id)
    )
    app_rec = (await db.execute(stmt)).scalar_one_or_none()
    if not app_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{application_id}' not found.",
        )

    if payload.status is not None:
        app_rec.status = payload.status
        # If moving to 'applied' and applied_at is not set, auto-stamp now
        if payload.status == "applied" and app_rec.applied_at is None and payload.applied_at is None:
            app_rec.applied_at = datetime.now(timezone.utc)

    if payload.applied_at is not None:
        app_rec.applied_at = payload.applied_at

    if payload.notes is not None:
        app_rec.notes = payload.notes

    await db.commit()
    await db.refresh(app_rec)
    return map_application_to_response(app_rec)


@router.delete(
    "/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an application record",
    description="Deletes an application and cascades deletion of attached documents.",
)
async def delete_application(
    application_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    stmt = select(Application).where(Application.id == application_id)
    app_rec = (await db.execute(stmt)).scalar_one_or_none()
    if not app_rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{application_id}' not found.",
        )

    await db.delete(app_rec)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- Document Attachment Sub-routes ---


@router.post(
    "/{application_id}/documents",
    response_model=GeneratedDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Attach a tailored document to an application",
    description="Attaches tailored resume bullets or a cover letter to the tracked application.",
)
async def attach_document(
    application_id: UUID,
    payload: GeneratedDocumentCreate,
    db: AsyncSession = Depends(get_db),
) -> GeneratedDocumentResponse:
    res_app = await db.execute(select(Application).where(Application.id == application_id))
    if not res_app.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application with ID '{application_id}' not found.",
        )

    new_doc = GeneratedDocument(
        id=uuid.uuid4(),
        application_id=application_id,
        doc_type=payload.doc_type,
        content=payload.content,
        is_approved_by_user=payload.is_approved_by_user,
    )
    db.add(new_doc)
    await db.commit()
    await db.refresh(new_doc)
    return GeneratedDocumentResponse.model_validate(new_doc)


@router.patch(
    "/{application_id}/documents/{document_id}",
    response_model=GeneratedDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update or approve a generated document",
    description="Updates document text content or toggles candidate approval (Human-in-the-Loop consent).",
)
async def update_document(
    application_id: UUID,
    document_id: UUID,
    payload: GeneratedDocumentUpdate,
    db: AsyncSession = Depends(get_db),
) -> GeneratedDocumentResponse:
    stmt = select(GeneratedDocument).where(
        GeneratedDocument.id == document_id,
        GeneratedDocument.application_id == application_id,
    )
    doc = (await db.execute(stmt)).scalar_one_or_none()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document '{document_id}' not found for application '{application_id}'.",
        )

    if payload.content is not None:
        doc.content = payload.content
    if payload.is_approved_by_user is not None:
        doc.is_approved_by_user = payload.is_approved_by_user

    await db.commit()
    await db.refresh(doc)
    return GeneratedDocumentResponse.model_validate(doc)
