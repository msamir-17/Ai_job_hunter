"""
Built-in Archetype Lens Configurations and Dynamic Role Classification Engine.
Allows the tailoring pipeline to adapt resume section order, skill priorities,
and bullet emphasis either via user preset selection or automatic JD keyword classification.
"""
import re
from typing import Dict, List
from app.schemas.archetype import ArchetypeClassificationResult, ArchetypeConfig


GENAI_ARCHETYPE = ArchetypeConfig(
    archetype_id="genai",
    display_name="Generative AI & LLM Specialist",
    description="Focuses on RAG pipelines, LLM agent workflows, evaluation benchmarking, and fact-checking guardrails.",
    section_order=["summary", "skills", "projects", "experience", "education"],
    skill_category_order=[
        "GenAI & LLMs",
        "AI & Machine Learning",
        "Backend & Systems",
        "Databases & Search",
        "DevOps & Engineering Practices",
    ],
    primary_angle="genai",
    max_projects=3,
    max_bullets_per_flagship=3,
    max_bullets_per_standard=2,
    headline_template="Generative AI & LLM Systems Engineer",
    summary_template=(
        "AI Engineer specializing in Retrieval-Augmented Generation (RAG), LLM evaluation benchmarking, "
        "and autonomous agent workflows. Track record of engineering zero-hallucination fact citation gates "
        "achieving 1.0 Faithfulness on Ragas suites and cutting multi-agent workflow latency 50% with asyncio."
    ),
    keywords=[
        "llm", "genai", "generative ai", "rag", "langchain", "langgraph", "ragas",
        "prompt engineering", "embeddings", "vector search", "agent", "agents",
        "huggingface", "gpt", "gemini", "fine-tuning", "hallucination",
    ],
)

SWE_ARCHETYPE = ArchetypeConfig(
    archetype_id="swe",
    display_name="Backend & Systems Software Engineer",
    description="Emphasizes scalable backend services, asynchronous concurrency, PostgreSQL databases, and clean SDLC.",
    section_order=["summary", "skills", "projects", "experience", "education"],
    skill_category_order=[
        "Backend & Systems",
        "Databases & Search",
        "DevOps & Engineering Practices",
        "AI & Machine Learning",
        "GenAI & LLMs",
    ],
    primary_angle="swe",
    max_projects=3,
    max_bullets_per_flagship=3,
    max_bullets_per_standard=2,
    headline_template="Backend Software Engineer | Python, FastAPI & Distributed Systems",
    summary_template=(
        "Backend Software Engineer with deep expertise in Python, FastAPI, and asynchronous system design. "
        "Experienced in architecting distributed PostgreSQL job queues with Dead Letter Queue retry semantics, "
        "implementing REST APIs with JWT authentication, and diagnosing concurrency bottlenecks."
    ),
    keywords=[
        "backend", "software engineer", "api", "fastapi", "django", "flask",
        "postgresql", "sql", "concurrency", "asyncio", "microservices", "docker",
        "rest", "distributed systems", "queue", "worker", "jwt", "sdlc",
    ],
)

AI_ENG_ARCHETYPE = ArchetypeConfig(
    archetype_id="ai_eng",
    display_name="Machine Learning & AI Platform Engineer",
    description="Balances classical ML, deep learning model training in PyTorch, dense vector search, and MLOps.",
    section_order=["summary", "skills", "projects", "experience", "education"],
    skill_category_order=[
        "AI & Machine Learning",
        "GenAI & LLMs",
        "Backend & Systems",
        "Databases & Search",
        "DevOps & Engineering Practices",
    ],
    primary_angle="ai_eng",
    max_projects=3,
    max_bullets_per_flagship=3,
    max_bullets_per_standard=2,
    headline_template="AI & Machine Learning Engineer | PyTorch, Embeddings & MLOps",
    summary_template=(
        "AI/ML Engineer specializing in dense vector embeddings, hybrid search calibration, and deep learning "
        "model training. Proven experience training custom Sequence-to-Sequence PyTorch models and building calibrated "
        "retrieval systems achieving NDCG@10 of 1.0 on ground-truth benchmark datasets."
    ),
    keywords=[
        "machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn",
        "model training", "nlp", "computer vision", "neural network", "transformer",
        "dense embeddings", "mlops", "bleu", "rocchio",
    ],
)

DATA_ARCHETYPE = ArchetypeConfig(
    archetype_id="data",
    display_name="Data & NLP Engineer",
    description="Focuses on unstructured document parsing, tabular extraction, vector search, and data quality.",
    section_order=["summary", "skills", "projects", "experience", "education"],
    skill_category_order=[
        "Databases & Search",
        "AI & Machine Learning",
        "Backend & Systems",
        "GenAI & LLMs",
        "DevOps & Engineering Practices",
    ],
    primary_angle="data",
    max_projects=3,
    max_bullets_per_flagship=3,
    max_bullets_per_standard=2,
    headline_template="Data & NLP Engineer | Search, Pipelines & PostgreSQL",
    summary_template=(
        "Data and NLP Engineer focused on high-volume document ingestion, tabular extraction, and vector databases. "
        "Experienced in implementing layout-aware document parsers achieving 100% Tabular Recall and managing "
        "PostgreSQL vector databases with hybrid BM25 search."
    ),
    keywords=[
        "data engineer", "etl", "pipeline", "nlp", "pandas", "numpy", "data analytics",
        "sql", "data processing", "tabular", "pdf parsing", "ingestion",
    ],
)

BUILTIN_ARCHETYPES: Dict[str, ArchetypeConfig] = {
    "genai": GENAI_ARCHETYPE,
    "swe": SWE_ARCHETYPE,
    "ai_eng": AI_ENG_ARCHETYPE,
    "data": DATA_ARCHETYPE,
}


def get_archetype(archetype_id: str) -> ArchetypeConfig:
    """Retrieve archetype configuration by id. Falls back to 'genai' if unknown."""
    return BUILTIN_ARCHETYPES.get(archetype_id.lower().strip(), GENAI_ARCHETYPE)


def list_available_archetypes() -> List[ArchetypeConfig]:
    """List all available pre-configured archetype presets."""
    return list(BUILTIN_ARCHETYPES.values())


def classify_job_archetype(
    job_title: str,
    job_description: str,
    skills_required: List[str] | None = None,
) -> ArchetypeClassificationResult:
    """
    Classify a target Job Description against available archetype lenses using weighted keyword scoring.
    Computes continuous relevance weights across all archetypes and picks the highest confidence match.
    """
    text_corpus = f"{job_title} {job_title} {' '.join(skills_required or [])} {job_description}".lower()

    raw_scores: Dict[str, float] = {}
    matched_keywords: List[str] = []

    for arch_id, config in BUILTIN_ARCHETYPES.items():
        score = 0.0
        # Title matches carry triple weight
        title_lower = job_title.lower()
        for kw in config.keywords:
            if re.search(r"\b" + re.escape(kw) + r"\b", title_lower):
                score += 3.0
                if kw not in matched_keywords:
                    matched_keywords.append(kw)
            elif re.search(r"\b" + re.escape(kw) + r"\b", text_corpus):
                score += 1.0
                if kw not in matched_keywords:
                    matched_keywords.append(kw)
        raw_scores[arch_id] = score

    total_score = sum(raw_scores.values())
    if total_score > 0:
        normalized_weights = {k: round(v / total_score, 4) for k, v in raw_scores.items()}
        best_archetype = max(normalized_weights, key=normalized_weights.get)
        confidence = normalized_weights[best_archetype]
    else:
        normalized_weights = {k: 0.25 for k in BUILTIN_ARCHETYPES.keys()}
        best_archetype = "genai"
        confidence = 0.25

    return ArchetypeClassificationResult(
        recommended_archetype_id=best_archetype,
        confidence_score=confidence,
        archetype_weights=normalized_weights,
        extracted_keywords=matched_keywords[:10],
    )
