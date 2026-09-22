from abc import ABC, abstractmethod
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseLLMProvider(ABC):
    """Abstract Base Class for all LLM providers in AI Job Hunter Co-Pilot."""

    @abstractmethod
    async def generate_structured(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: Type[T],
    ) -> T:
        """
        Generate structured output conforming strictly to response_schema.

        Args:
            system_prompt: System-level instruction/guardrails.
            user_prompt: User input data to process.
            response_schema: Pydantic BaseModel subclass defining the output JSON schema.

        Returns:
            Validated instance of response_schema.
        """
        pass
