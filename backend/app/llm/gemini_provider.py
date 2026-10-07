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
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model

    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
    ) -> T:
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in settings or environment.")

        start_time = time.time()

        try:
            client = genai.Client(api_key=self.api_key)
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

