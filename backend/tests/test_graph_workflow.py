import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.graph.edges import (
    should_continue_after_deterministic,
    should_continue_after_load,
    should_continue_after_vector,
)
from app.graph.nodes import MatchingWorkflowNodes
from app.graph.state import JobHunterState
from app.graph.workflow import create_matching_graph
from app.models import CandidateProfile, Job, JobMatch
from app.schemas.matching import (
    JobFilterResult,
    JobMatchAnalysisResult,
    RuleResult,
    SkillGapAnalysis,
)
from app.services.deterministic_filter import DeterministicFilterService
from app.services.llm_matching import LLMMatchingService
from app.services.vector_search import VectorSearchService


@pytest.fixture
def anyio_backend():
    return "asyncio"


def test_conditional_edges_routing():
    """Verify conditional edge routing functions logic."""
    # 1. should_continue_after_load
    assert should_continue_after_load({"error_message": "Not found"}) == "save_results"
    assert should_continue_after_load({"error_message": None}) == "deterministic_filter"

    # 2. should_continue_after_deterministic
    assert should_continue_after_deterministic({"passed_deterministic": False, "deterministic_status": "rejected"}) == "disqualify_job"
    assert should_continue_after_deterministic({"passed_deterministic": True, "deterministic_status": "shortlisted"}) == "vector_similarity"
    assert should_continue_after_deterministic({"passed_deterministic": True, "deterministic_status": "review"}) == "vector_similarity"

    # 3. should_continue_after_vector
    assert should_continue_after_vector({"vector_passed": False}) == "mark_low_match"
    assert should_continue_after_vector({"vector_passed": True}) == "llm_gap_analysis"


@pytest.mark.anyio
async def test_graph_stage1_disqualification_bypasses_vector_and_llm():
    """
    Verify that when Stage 1 deterministic filter rejects a job,
    the workflow routes directly to disqualify_job -> save_results,
    bypassing vector similarity and LLM analysis completely.
    """
    candidate_id = uuid.uuid4()
    job_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()

    candidate = CandidateProfile(id=candidate_id, headline="Fresher Dev", skills=["Python"])
    job = Job(id=job_id, title="Senior ML Director", company="BigTech", is_remote=False)

    # Mock DB queries: load_data (cand, job), deterministic (cand, job), save_results (existing match)
    mock_res_cand = MagicMock()
    mock_res_cand.scalar_one_or_none.return_value = candidate
    mock_res_cand.scalar_one.return_value = candidate

    mock_res_job = MagicMock()
    mock_res_job.scalar_one_or_none.return_value = job
    mock_res_job.scalar_one.return_value = job

    mock_res_match = MagicMock()
    mock_res_match.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [
        mock_res_cand,  # load_data cand
        mock_res_job,   # load_data job
        mock_res_cand,  # deterministic cand
        mock_res_job,   # deterministic job
        mock_res_match, # save_results
    ]

    mock_filter_service = MagicMock(spec=DeterministicFilterService)
    mock_filter_service.evaluate_job.return_value = JobFilterResult(
        job_id=job_id,
        candidate_profile_id=candidate_id,
        title=job.title,
        company=job.company,
        overall_status="rejected",
        passed_deterministic=False,
        rule_results=[RuleResult(rule_name="experience", status="reject", reason_code="GAP", explanation="5 yr gap")],
        summary_explanation="Candidate lacks required senior experience.",
        matched_skills=[],
        missing_skills=[],
    )

    mock_vector_service = AsyncMock(spec=VectorSearchService)
    mock_llm_service = AsyncMock(spec=LLMMatchingService)

    nodes = MatchingWorkflowNodes(
        db=mock_db,
        filter_service=mock_filter_service,
        vector_service=mock_vector_service,
        llm_service=mock_llm_service,
    )

    graph = create_matching_graph(nodes=nodes)
    initial_state: JobHunterState = {
        "candidate_profile_id": str(candidate_id),
        "job_id": str(job_id),
    }

    final_state = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "test_thread_1"}},
    )

    assert final_state["passed_deterministic"] is False
    assert final_state["overall_status"] == "rejected"
    assert "Disqualified" in final_state["analysis_summary"] or "lacks" in final_state["analysis_summary"]

    # Verify vector and LLM services were NEVER called (bypassed)
    mock_vector_service.ensure_candidate_embedding.assert_not_called()
    mock_llm_service.evaluate_match.assert_not_called()
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_graph_stage2_low_vector_bypasses_llm():
    """
    Verify that when Stage 2 vector similarity is below threshold (< 0.3),
    the workflow marks low match and routes directly to save_results,
    bypassing Stage 3 LLM analysis.
    """
    candidate_id = uuid.uuid4()
    job_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()

    candidate = CandidateProfile(id=candidate_id, headline="AI Engineer", embedding=[1.0] + [0.0] * 383)
    job = Job(id=job_id, title="Accountant", company="Finance Co", embedding=[0.0] * 383 + [1.0])

    mock_res_cand = MagicMock()
    mock_res_cand.scalar_one_or_none.return_value = candidate
    mock_res_cand.scalar_one.return_value = candidate

    mock_res_job = MagicMock()
    mock_res_job.scalar_one_or_none.return_value = job
    mock_res_job.scalar_one.return_value = job

    mock_res_match = MagicMock()
    mock_res_match.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [
        mock_res_cand,  # load_data cand
        mock_res_job,   # load_data job
        mock_res_cand,  # deterministic cand
        mock_res_job,   # deterministic job
        mock_res_cand,  # vector cand
        mock_res_job,   # vector job
        mock_res_match, # save_results
    ]

    mock_filter_service = MagicMock(spec=DeterministicFilterService)
    mock_filter_service.evaluate_job.return_value = JobFilterResult(
        job_id=job_id,
        candidate_profile_id=candidate_id,
        title=job.title,
        company=job.company,
        overall_status="shortlisted",
        passed_deterministic=True,
        rule_results=[],
        summary_explanation="Passed deterministic checks.",
        matched_skills=[],
        missing_skills=[],
    )

    mock_vector_service = AsyncMock(spec=VectorSearchService)
    mock_vector_service.ensure_candidate_embedding.return_value = candidate.embedding
    mock_llm_service = AsyncMock(spec=LLMMatchingService)

    nodes = MatchingWorkflowNodes(
        db=mock_db,
        filter_service=mock_filter_service,
        vector_service=mock_vector_service,
        llm_service=mock_llm_service,
    )

    graph = create_matching_graph(nodes=nodes)
    initial_state: JobHunterState = {
        "candidate_profile_id": str(candidate_id),
        "job_id": str(job_id),
    }

    final_state = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "test_thread_2"}},
    )

    assert final_state["passed_deterministic"] is True
    assert final_state["vector_passed"] is False
    assert final_state["overall_status"] == "rejected"
    assert "Disqualified in Stage 2" in final_state["analysis_summary"]

    # Verify LLM service was NEVER called
    mock_llm_service.evaluate_match.assert_not_called()
    mock_db.commit.assert_called_once()


@pytest.mark.anyio
async def test_graph_full_success_pipeline():
    """
    Verify complete 3-stage execution when candidate passes deterministic,
    has high vector similarity, and receives a high LLM score.
    """
    candidate_id = uuid.uuid4()
    job_id = uuid.uuid4()

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.add = MagicMock()

    candidate = CandidateProfile(id=candidate_id, headline="AI Engineer", embedding=[1.0] + [0.0] * 383)
    job = Job(id=job_id, title="ML Engineer", company="AI Corp", embedding=[0.95] + [0.31] + [0.0] * 382)

    mock_res_cand = MagicMock()
    mock_res_cand.scalar_one_or_none.return_value = candidate
    mock_res_cand.scalar_one.return_value = candidate

    mock_res_job = MagicMock()
    mock_res_job.scalar_one_or_none.return_value = job
    mock_res_job.scalar_one.return_value = job

    mock_res_match = MagicMock()
    mock_res_match.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [
        mock_res_cand,  # load_data cand
        mock_res_job,   # load_data job
        mock_res_cand,  # deterministic cand
        mock_res_job,   # deterministic job
        mock_res_cand,  # vector cand
        mock_res_job,   # vector job
        mock_res_cand,  # llm cand
        mock_res_job,   # llm job
        mock_res_match, # save_results
    ]

    mock_filter_service = MagicMock(spec=DeterministicFilterService)
    mock_filter_service.evaluate_job.return_value = JobFilterResult(
        job_id=job_id,
        candidate_profile_id=candidate_id,
        title=job.title,
        company=job.company,
        overall_status="shortlisted",
        passed_deterministic=True,
        rule_results=[],
        summary_explanation="Passed deterministic checks.",
        matched_skills=["Python"],
        missing_skills=[],
    )

    mock_vector_service = AsyncMock(spec=VectorSearchService)
    mock_vector_service.ensure_candidate_embedding.return_value = candidate.embedding

    mock_llm_service = AsyncMock(spec=LLMMatchingService)
    mock_llm_service.evaluate_match.return_value = JobMatchAnalysisResult(
        job_id=job_id,
        candidate_profile_id=candidate_id,
        title=job.title,
        company=job.company,
        passed_deterministic=True,
        vector_score=0.95,
        llm_score=92,
        matched_skills=["Python", "PyTorch"],
        missing_skills=[],
        missing_required_skills=[],
        missing_preferred_skills=[],
        analysis_summary="Outstanding match.",
        recommendation="strong_match",
        status="shortlisted",
    )

    nodes = MatchingWorkflowNodes(
        db=mock_db,
        filter_service=mock_filter_service,
        vector_service=mock_vector_service,
        llm_service=mock_llm_service,
    )

    graph = create_matching_graph(nodes=nodes)
    initial_state: JobHunterState = {
        "candidate_profile_id": str(candidate_id),
        "job_id": str(job_id),
    }

    final_state = await graph.ainvoke(
        initial_state,
        config={"configurable": {"thread_id": "test_thread_3"}},
    )

    assert final_state["passed_deterministic"] is True
    assert final_state["vector_passed"] is True
    assert final_state["vector_score"] > 0.9
    assert final_state["llm_score"] == 92
    assert final_state["overall_status"] == "shortlisted"
    assert final_state["recommendation"] == "strong_match"

    mock_llm_service.evaluate_match.assert_called_once()
    mock_db.commit.assert_called_once()
