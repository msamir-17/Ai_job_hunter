import os
import time
from typing import Type, TypeVar
from google import genai
from google.genai import types
from pydantic import BaseModel

from app.config import settings
from app.llm.base import BaseLLMProvider
from app.llm.telemetry import LLMTelemetryTracker

T = TypeVar("T", bound=BaseModel)


class GeminiLLMProvider(BaseLLMProvider):
    """
    Gemini LLM Provider implementation using the official google-genai SDK.
    Includes structured logging, latency tracking, token usage, and cost tracking telemetry.
    """

    def __init__(self, api_key: str | None = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model

    def _get_api_key(self) -> str:
        key = self.api_key or settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        if not key or key.strip() in ("", "your_gemini_api_key_here"):
            from pathlib import Path
            from dotenv import dotenv_values
            for env_path in [
                Path(__file__).resolve().parent.parent.parent / ".env",
                Path(__file__).resolve().parent.parent.parent.parent / ".env",
            ]:
                if env_path.exists():
                    vals = dotenv_values(env_path)
                    candidate = vals.get("GEMINI_API_KEY", "")
                    if candidate and candidate.strip() not in ("", "your_gemini_api_key_here"):
                        key = candidate
                        break
        return key.strip() if key else ""

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
    ) -> T:
        api_key = self._get_api_key()
        if not api_key or api_key in ("", "your_gemini_api_key_here"):
            raise ValueError(
                "Gemini API key is not configured. Please add a valid GEMINI_API_KEY to your .env file."
            )

        start_time = time.time()

        try:
            client = genai.Client(api_key=api_key)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                response_mime_type="application/json",
                response_schema=response_schema,
                temperature=settings.LLM_TEMPERATURE,
            )

            response = await client.aio.models.generate_content(
                model=self.model,
                contents=user_prompt,
                config=config,
            )

            if not response.text:
                raise ValueError("Empty response returned from Gemini LLM provider.")

            usage = getattr(response, "usage_metadata", None)
            LLMTelemetryTracker.log_llm_call(
                model_name=self.model,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                response_text=response.text,
                start_time=start_time,
                usage_metadata=usage
            )

            return response_schema.model_validate_json(response.text)

        except ValueError:
            raise
        except Exception as e:
            raise RuntimeError(f"Gemini LLM generation failed: {str(e)}")

