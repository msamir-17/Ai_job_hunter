from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.auth import router as auth_router
from app.api.candidate_profile import router as candidate_profile_router
from app.api.jobs import router as jobs_router
from app.api.matching import router as matching_router
from app.api.resume import router as resume_router
from app.api.tailoring import router as tailoring_router
from app.api.applications import router as applications_router
from app.api.feedback import router as feedback_router
from app.api.screening_qa import router as screening_qa_router
from app.api.settings import router as settings_router

app = FastAPI(
    title="AI Job Hunter Co-Pilot API",
    description="Backend API for AI Job Hunter Co-Pilot application",
    version="0.1.0",
)

# Register API Routers
app.include_router(auth_router)
app.include_router(candidate_profile_router)
app.include_router(resume_router)
app.include_router(jobs_router)
app.include_router(matching_router)
app.include_router(tailoring_router)
app.include_router(applications_router)
app.include_router(feedback_router)
app.include_router(screening_qa_router)
app.include_router(settings_router)


# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.database import get_db
from app.models import User

@app.get("/health", tags=["Health"])
async def health_check():
    """Minimal public health check returning operational status."""
    return {"status": "ok"}

@app.get("/api/v1/admin/health", tags=["Admin & Diagnostics"])
async def admin_health_check(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Detailed operational diagnostics for authenticated users."""
    db_status = "connected"
    try:
        await db.execute(select(1))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "service": "AI Job Hunter Co-Pilot API",
        "environment": settings.ENVIRONMENT,
        "active_llm_provider": settings.ACTIVE_LLM_PROVIDER,
        "database": db_status,
        "authenticated_user": current_user.email,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
