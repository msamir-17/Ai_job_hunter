"""
LLM Observability, Latency, Token Usage & Cost Tracking Module.
Logs structured JSON telemetry metrics for LLM calls and supports optional Langfuse tracing.
"""
import time
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ai_job_hunter.llm_telemetry")
logging.basicConfig(level=logging.INFO)

# Pricing per million tokens (USD)
LLM_PRICING: Dict[str, Dict[str, float]] = {
    "gemini-2.5-flash": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gemini-1.5-flash": {"input_per_m": 0.075, "output_per_m": 0.30},
    "gemini-1.5-pro": {"input_per_m": 1.25, "output_per_m": 5.00},
    "gpt-4o-mini": {"input_per_m": 0.15, "output_per_m": 0.60},
}


class LLMTelemetryTracker:
    """Tracks latency, token usage, cost, and emits structured logs per LLM request."""

    @staticmethod
    def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate estimated cost in USD based on model pricing."""
        pricing = LLM_PRICING.get(model_name, LLM_PRICING["gemini-2.5-flash"])
        input_cost = (input_tokens / 1_000_000.0) * pricing["input_per_m"]
        output_cost = (output_tokens / 1_000_000.0) * pricing["output_per_m"]
        return round(input_cost + output_cost, 6)

    @staticmethod
    def log_llm_call(
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        response_text: str,
        start_time: float,
        usage_metadata: Optional[Any] = None
    ) -> Dict[str, Any]:
        """Record and log structured telemetry data for LLM invocation."""
        elapsed_sec = round(time.time() - start_time, 4)

        # Estimate tokens if SDK metadata is not available
        input_tokens = getattr(usage_metadata, "prompt_token_count", None) if usage_metadata else None
        output_tokens = getattr(usage_metadata, "candidates_token_count", None) if usage_metadata else None

        if input_tokens is None:
            input_tokens = len((system_prompt + user_prompt).split()) * 4 // 3
        if output_tokens is None:
            output_tokens = len(response_text.split()) * 4 // 3

        cost_usd = LLMTelemetryTracker.calculate_cost(model_name, input_tokens, output_tokens)

        telemetry_data = {
            "event": "llm_invocation",
            "model": model_name,
            "latency_seconds": elapsed_sec,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost_usd": cost_usd,
            "status": "success"
        }

        logger.info(
            f"[LLM TELEMETRY] Model={model_name} | Latency={elapsed_sec}s | Tokens={input_tokens}in/{output_tokens}out | Cost=${cost_usd:.6f}"
        )

        return telemetry_data
