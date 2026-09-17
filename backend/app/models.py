import uuid
from datetime import datetime
from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Boolean, Float, Integer


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class User(Base):
    """Application user/account."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    candidate_profile: Mapped["CandidateProfile | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class CandidateProfile(Base):
    """Structured candidate profile used for job matching."""

    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    headline: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    skills: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    experience: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    education: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    target_titles: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
    Vector(384),
    nullable=True,
    )

    # VECTOR(384) will be added after pgvector's SQLAlchemy integration
    # is configured in the next database step.

    user: Mapped["User"] = relationship(
        back_populates="candidate_profile",
    )

    resumes: Mapped[list["Resume"]] = relationship(
        back_populates="candidate_profile",
        cascade="all, delete-orphan",
    )

    job_matches: Mapped[list["JobMatch"]] = relationship(
    back_populates="candidate_profile",
    cascade="all, delete-orphan",
    )



class Resume(Base):
    """Uploaded resume and its extracted/parsed content."""

    __tablename__ = "resumes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id"),
        nullable=False,
    )

    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    parsed_json: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    candidate_profile: Mapped["CandidateProfile"] = relationship(
        back_populates="resumes",
    )

class Job(Base):
    """Job posting stored for search and candidate matching."""

    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )

    company: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_remote: Mapped[bool] = mapped_column(
        nullable=False,
        default=False,
    )

    salary_min: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    salary_max: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    description_raw: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    skills_required: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    url: Mapped[str | None] = mapped_column(
        String(1024),
        nullable=True,
    )

    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(384),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    job_matches: Mapped[list["JobMatch"]] = relationship(
    back_populates="job",
    cascade="all, delete-orphan",
    )

class JobMatch(Base):
    """Stores the matching analysis between a candidate profile and a job."""

    __tablename__ = "job_matches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    candidate_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("candidate_profiles.id"),
        nullable=False,
    )

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jobs.id"),
        nullable=False,
    )

    passed_deterministic: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    vector_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    llm_score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    matched_skills: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    missing_skills: Mapped[list | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    analysis_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    candidate_profile: Mapped["CandidateProfile"] = relationship(
        back_populates="job_matches",
    )

    job: Mapped["Job"] = relationship(
        back_populates="job_matches",
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="job_match",
        cascade="all, delete-orphan",
    )

class Application(Base):
    """Tracks a user's application for a matched job."""

    __tablename__ = "applications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    job_match_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("job_matches.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="saved",
    )

    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    job_match: Mapped["JobMatch"] = relationship(
        back_populates="applications",
    )

