"""
Settings & AI Provider Disclosure Endpoints.
Discloses active LLM provider, third-party data processing terms, and privacy metadata.
"""
from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/v1/settings", tags=["Settings & Privacy"])

PROVIDER_POLICIES = {
    "gemini": {
        "display_name": "Google Gemini",
        "policy_url": "https://ai.google.dev/terms",
        "privacy_notice": (
            "Resume text and job descriptions are processed by Google AI APIs for skill extraction and semantic matching. "
            "Review Google AI terms for details on how data is handled."
        ),
    },
    "groq": {
        "display_name": "Groq Cloud LPU",
        "policy_url": "https://groq.com/terms-of-use/",
        "privacy_notice": (
            "Fast inference powered by Groq LPUs. Data is processed in accordance with Groq terms."
        ),
    },
    "mistral": {
        "display_name": "Mistral AI",
        "policy_url": "https://mistral.ai/terms/",
        "privacy_notice": (
            "Inference processed via Mistral AI endpoints in compliance with GDPR and Mistral terms."
        ),
    },
}


@router.get("/llm-provider")
async def get_llm_provider_info():
    """
    Public disclosure endpoint returning active AI provider, policy URL, and privacy notice.
    Allows frontend to present clear third-party consent before sending candidate data.
    """
    provider_key = (settings.ACTIVE_LLM_PROVIDER or "gemini").lower()
    info = PROVIDER_POLICIES.get(
        provider_key,
        {
            "display_name": provider_key.title(),
            "policy_url": "https://ai.google.dev/terms",
            "privacy_notice": "AI inferences are processed through third-party LLM APIs.",
        },
    )
    return {
        "active_provider": provider_key,
        "display_name": info["display_name"],
        "policy_url": info["policy_url"],
        "privacy_notice": info["privacy_notice"],
        "is_third_party": True,
    }
