from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.gemini_provider import GeminiLLMProvider


def get_llm_provider() -> BaseLLMProvider:
    """
    Factory function returning the configured active LLM provider.

    Currently supports: 'gemini' (extensible to 'groq', 'mistral' in future phases).
    """
    provider_name = settings.ACTIVE_LLM_PROVIDER.lower().strip()
    if provider_name == "gemini":
        return GeminiLLMProvider()
    else:
        raise ValueError(
            f"Unsupported LLM provider '{settings.ACTIVE_LLM_PROVIDER}'. "
            f"Currently supported providers: 'gemini'."
        )
