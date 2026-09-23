from app.api.candidate_profile import router as candidate_profile_router
from app.api.jobs import router as jobs_router
from app.api.resume import router as resume_router

__all__ = ["candidate_profile_router", "jobs_router", "resume_router"]
