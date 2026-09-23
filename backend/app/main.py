from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.candidate_profile import router as candidate_profile_router
from app.api.jobs import router as jobs_router
from app.api.resume import router as resume_router

app = FastAPI(
    title="AI Job Hunter Co-Pilot API",
    description="Backend API for AI Job Hunter Co-Pilot application",
    version="0.1.0",
)

# Register API Routers
app.include_router(candidate_profile_router)
app.include_router(resume_router)
app.include_router(jobs_router)


# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend operational status."""
    return {
        "status": "ok",
        "service": "AI Job Hunter Co-Pilot API",
        "environment": settings.ENVIRONMENT,
        "active_llm_provider": settings.ACTIVE_LLM_PROVIDER,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
