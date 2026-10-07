"""
Unit tests for LLM Telemetry, token usage, latency, and cost tracking.
"""
import pytest
from app.llm.telemetry import LLMTelemetryTracker


def test_calculate_cost_gemini_2_5_flash():
    """Test cost calculation for Gemini 2.5 Flash model."""
    cost = LLMTelemetryTracker.calculate_cost("gemini-2.5-flash", input_tokens=1_000_000, output_tokens=1_000_000)
    # $0.075 input + $0.30 output = $0.375
    assert cost == pytest.approx(0.375, rel=1e-3)


def test_calculate_cost_fallback():
    """Test cost calculation fallback for unknown model name."""
    cost = LLMTelemetryTracker.calculate_cost("unknown-model", input_tokens=500_000, output_tokens=500_000)
    assert cost > 0.0


def test_log_llm_call_telemetry():
    """Test structured log telemetry payload generation."""
    telemetry = LLMTelemetryTracker.log_llm_call(
        model_name="gemini-2.5-flash",
        system_prompt="You are a helpful assistant.",
        user_prompt="Analyze this job.",
        response_text="Structured match analysis result.",
        start_time=100.0,
        usage_metadata=None
    )
    
    assert telemetry["event"] == "llm_invocation"
    assert telemetry["model"] == "gemini-2.5-flash"
    assert telemetry["input_tokens"] > 0
    assert telemetry["output_tokens"] > 0
    assert telemetry["estimated_cost_usd"] > 0.0
    assert telemetry["status"] == "success"
