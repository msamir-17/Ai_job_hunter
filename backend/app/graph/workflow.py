from typing import Any
from uuid import UUID

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.graph.edges import (
    should_continue_after_deterministic,
    should_continue_after_load,
    should_continue_after_vector,
)
from app.graph.nodes import MatchingWorkflowNodes
from app.graph.state import JobHunterState
from app.llm.base import BaseLLMProvider


def create_matching_graph(
    nodes: MatchingWorkflowNodes,
    checkpointer: Any | None = None,
):
    """
    Construct and compile the stateful LangGraph matching workflow.
    """
    workflow = StateGraph(JobHunterState)

    # 1. Register nodes
    workflow.add_node("load_data", nodes.load_data)
    workflow.add_node("deterministic_filter", nodes.deterministic_filter)
    workflow.add_node("disqualify_job", nodes.disqualify_job)
    workflow.add_node("vector_similarity", nodes.vector_similarity)
    workflow.add_node("mark_low_match", nodes.mark_low_match)
    workflow.add_node("llm_gap_analysis", nodes.llm_gap_analysis)
    workflow.add_node("save_results", nodes.save_results)

    # 2. Wire entry point
    workflow.add_edge(START, "load_data")

    # 3. Wire conditional transition after load_data
    workflow.add_conditional_edges(
        "load_data",
        should_continue_after_load,
        {
            "deterministic_filter": "deterministic_filter",
            "save_results": "save_results",
        },
    )

    # 4. Wire conditional transition after Stage 1 deterministic filter
    workflow.add_conditional_edges(
        "deterministic_filter",
        should_continue_after_deterministic,
        {
            "disqualify_job": "disqualify_job",
            "vector_similarity": "vector_similarity",
        },
    )

    # Disqualification bypasses vector and LLM stages directly to save_results
    workflow.add_edge("disqualify_job", "save_results")

    # 5. Wire conditional transition after Stage 2 vector similarity
    workflow.add_conditional_edges(
        "vector_similarity",
        should_continue_after_vector,
        {
            "mark_low_match": "mark_low_match",
            "llm_gap_analysis": "llm_gap_analysis",
        },
    )

    # Low vector similarity bypasses LLM stage directly to save_results
    workflow.add_edge("mark_low_match", "save_results")

    # 6. Wire Stage 3 LLM analysis to save_results
    workflow.add_edge("llm_gap_analysis", "save_results")

    # 7. Wire save_results to termination
    workflow.add_edge("save_results", END)

    # Use MemorySaver checkpointer if provided
    cp = checkpointer if checkpointer is not None else MemorySaver()
    return workflow.compile(checkpointer=cp)


async def run_matching_pipeline(
    db: AsyncSession,
    candidate_profile_id: UUID,
    job_id: UUID,
    llm_provider: BaseLLMProvider | None = None,
    checkpointer: Any | None = None,
) -> JobHunterState:
    """
    Execute the compiled LangGraph matching pipeline end-to-end for a candidate and job.
    """
    from app.services.deterministic_filter import DeterministicFilterService
    from app.services.llm_matching import LLMMatchingService
    from app.services.vector_search import VectorSearchService

    filter_service = DeterministicFilterService()
    vector_service = VectorSearchService(db=db)
    llm_service = LLMMatchingService(db=db, provider=llm_provider)

    nodes = MatchingWorkflowNodes(
        db=db,
        filter_service=filter_service,
        vector_service=vector_service,
        llm_service=llm_service,
    )

    app_graph = create_matching_graph(nodes=nodes, checkpointer=checkpointer)

    initial_state: JobHunterState = {
        "candidate_profile_id": str(candidate_profile_id),
        "job_id": str(job_id),
    }

    config = {"configurable": {"thread_id": f"{candidate_profile_id}_{job_id}"}}
    final_state = await app_graph.ainvoke(initial_state, config=config)
    return final_state
