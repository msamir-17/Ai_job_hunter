"""
Hybrid Search & Reranking Service for AI Job Hunter.
Combines BM25 lexical keyword search with dense vector similarity and section-level chunking.
Solves 256-token MiniLM truncation by extracting requirements/skills text before embedding.
"""
import re
import math
from typing import Dict, List, Tuple, Any


def extract_requirements_chunk(description_raw: str | None, title: str = "") -> str:
    """
    Extract requirements and skills section from raw job description.
    Prevents MiniLM-L6 256-token truncation from throwing away core skill requirements.
    """
    if not description_raw:
        return title

    lines = description_raw.split("\n")
    req_keywords = [
        "requirement", "qualification", "skills", "must have", "what we are looking for",
        "who you are", "tech stack", "responsibilities", "nice to have", "profile"
    ]

    req_lines = []
    capture = False

    for line in lines:
        line_lower = line.strip().lower()
        if any(kw in line_lower for kw in req_keywords):
            capture = True
        if capture:
            req_lines.append(line.strip())

    # If section headers were found, return extracted chunk
    if len(req_lines) >= 3:
        chunk = "\n".join(req_lines[:15]) # Limit to ~200 tokens
        return f"{title}\n{chunk}"

    # Fall back to taking the middle-to-end of description where requirements usually live
    tokens = description_raw.split()
    if len(tokens) > 150:
        # Take title + middle 150 tokens
        middle_tokens = tokens[50:200]
        return f"{title}\n" + " ".join(middle_tokens)

    return f"{title}\n{description_raw}"


class BM25Searcher:
    """In-memory BM25 implementation for lexical keyword relevance scoring."""

    def __init__(self, corpus: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lengths = []
        self.doc_freqs: Dict[str, int] = {}
        self.doc_term_freqs: List[Dict[str, int]] = []

        for doc in corpus:
            tokens = self._tokenize(doc)
            self.doc_lengths.append(len(tokens))
            term_freq: Dict[str, int] = {}
            for t in tokens:
                term_freq[t] = term_freq.get(t, 0) + 1
            self.doc_term_freqs.append(term_freq)
            
            for t in set(tokens):
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = sum(self.doc_lengths) / self.corpus_size if self.corpus_size > 0 else 1.0

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [t for t in cleaned.split() if len(t) > 1]

    def score(self, query: str, doc_idx: int) -> float:
        """Calculate BM25 score for a query against a document index."""
        query_tokens = self._tokenize(query)
        doc_len = self.doc_lengths[doc_idx]
        term_freqs = self.doc_term_freqs[doc_idx]
        
        score = 0.0
        for token in query_tokens:
            if token not in term_freqs:
                continue
            f = term_freqs[token]
            df = self.doc_freqs.get(token, 0)
            idf = math.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)
            
            num = f * (self.k1 + 1.0)
            den = f + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
            score += idf * (num / den)

        return score


def calculate_hybrid_score(
    dense_vector_score: float,
    bm25_score: float,
    alpha: float = 0.7
) -> float:
    """
    Combine Dense Vector Similarity and BM25 Lexical score.
    alpha = weight given to dense vector (default 0.7 dense, 0.3 lexical).
    """
    # Normalize BM25 score using sigmoid mapping to [0, 1] range
    norm_bm25 = 1.0 / (1.0 + math.exp(-bm25_score / 5.0))
    hybrid_score = (alpha * dense_vector_score) + ((1.0 - alpha) * norm_bm25)
    return round(hybrid_score, 4)


def cross_encoder_rerank(
    candidate_profile_text: str,
    top_jobs: List[Dict[str, Any]],
    top_k: int = 10
) -> List[Dict[str, Any]]:
    """
    Rerank top 50 retrieved jobs using exact term interaction & requirement coverage heuristics.
    """
    cand_tokens = set(re.sub(r"[^\w\s]", " ", candidate_profile_text.lower()).split())
    
    for job in top_jobs:
        job_req = job.get("requirements_text", job.get("description_raw", ""))
        job_tokens = set(re.sub(r"[^\w\s]", " ", job_req.lower()).split())
        
        # Exact skill & term overlap penalty/boost
        common = cand_tokens.intersection(job_tokens)
        overlap_ratio = len(common) / max(1, len(job_tokens))
        
        # Combine hybrid score with cross interaction boost
        initial_score = job.get("score", 0.0)
        reranked_score = (0.8 * initial_score) + (0.2 * overlap_ratio)
        job["reranked_score"] = round(reranked_score, 4)

    # Sort descending by reranked_score
    top_jobs.sort(key=lambda x: x["reranked_score"], reverse=True)
    return top_jobs[:top_k]
