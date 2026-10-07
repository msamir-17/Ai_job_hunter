"""
Information Retrieval (IR) evaluation metrics for candidate-job matching pipelines.
Calculates Precision@K, Recall@K, NDCG@K, and Stage 1 False Negative Rate.
"""
import math
from typing import Dict, List, Set


def precision_at_k(retrieved_ids: List[str], ground_truth: Dict[str, int], k: int = 10, min_relevance: int = 1) -> float:
    """
    Calculate Precision@K: Fraction of top K retrieved jobs that are relevant.
    Relevance is considered True if ground_truth[job_id] >= min_relevance.
    """
    if not retrieved_ids or k <= 0:
        return 0.0
    
    top_k = retrieved_ids[:k]
    relevant_count = sum(1 for job_id in top_k if ground_truth.get(job_id, 0) >= min_relevance)
    return relevant_count / len(top_k)


def recall_at_k(retrieved_ids: List[str], ground_truth: Dict[str, int], k: int = 10, min_relevance: int = 1) -> float:
    """
    Calculate Recall@K: Fraction of total relevant jobs that are retrieved in top K.
    """
    total_relevant = sum(1 for grade in ground_truth.values() if grade >= min_relevance)
    if total_relevant == 0:
        return 0.0
    
    top_k = retrieved_ids[:k]
    retrieved_relevant = sum(1 for job_id in top_k if ground_truth.get(job_id, 0) >= min_relevance)
    return retrieved_relevant / total_relevant


def dcg_at_k(retrieved_ids: List[str], ground_truth: Dict[str, int], k: int = 10) -> float:
    """
    Calculate Discounted Cumulative Gain at rank K (DCG@K).
    """
    dcg = 0.0
    for i, job_id in enumerate(retrieved_ids[:k]):
        rel = float(ground_truth.get(job_id, 0))
        # 1-indexed rank = i + 1
        dcg += (2**rel - 1.0) / math.log2(i + 2)
    return dcg


def ndcg_at_k(retrieved_ids: List[str], ground_truth: Dict[str, int], k: int = 10) -> float:
    """
    Calculate Normalized Discounted Cumulative Gain at rank K (NDCG@K).
    Compares actual DCG@K against Ideal DCG@K (IDCG@K).
    """
    actual_dcg = dcg_at_k(retrieved_ids, ground_truth, k)
    if actual_dcg == 0.0:
        return 0.0
    
    # Calculate IDCG by sorting all ground truth grades in descending order
    ideal_relevances = sorted(ground_truth.values(), reverse=True)[:k]
    idcg = 0.0
    for i, rel in enumerate(ideal_relevances):
        idcg += (2**float(rel) - 1.0) / math.log2(i + 2)
        
    if idcg == 0.0:
        return 0.0
    
    return actual_dcg / idcg


def evaluate_stage1_filtering(
    rejected_ids: Set[str],
    passed_ids: Set[str],
    ground_truth: Dict[str, int],
    min_relevance: int = 1
) -> Dict[str, float]:
    """
    Evaluate Stage 1 Filter:
    - Pass Rate: % of candidate jobs passed
    - False Negative Rate: % of good jobs (relevance >= min_relevance) that were falsely rejected by Stage 1
    """
    total_jobs = len(ground_truth)
    if total_jobs == 0:
        return {"pass_rate": 0.0, "false_negative_rate": 0.0, "true_negative_rate": 0.0}
    
    total_relevant = sum(1 for rel in ground_truth.values() if rel >= min_relevance)
    total_irrelevant = total_jobs - total_relevant
    
    false_negatives = sum(1 for job_id in rejected_ids if ground_truth.get(job_id, 0) >= min_relevance)
    true_negatives = sum(1 for job_id in rejected_ids if ground_truth.get(job_id, 0) < min_relevance)
    
    fnr = false_negatives / total_relevant if total_relevant > 0 else 0.0
    tnr = true_negatives / total_irrelevant if total_irrelevant > 0 else 0.0
    pass_rate = len(passed_ids) / total_jobs if total_jobs > 0 else 0.0
    
    return {
        "pass_rate": round(pass_rate, 4),
        "false_negative_rate": round(fnr, 4),
        "true_negative_rate": round(tnr, 4),
        "false_negatives_count": false_negatives,
        "total_relevant": total_relevant,
    }
