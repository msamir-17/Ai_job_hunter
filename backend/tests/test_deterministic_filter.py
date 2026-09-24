import datetime
import uuid

from app.models import CandidateProfile, Job
from app.schemas.matching import FilterConfig
from app.services.deterministic_filter import (
    DeterministicFilterService,
    calculate_candidate_experience_years,
    extract_job_required_experience,
    parse_date,
)


def test_parse_date():
    """Verify parsing various valid and invalid date formats."""
    assert parse_date("2022-05-15") == datetime.date(2022, 5, 15)
    assert parse_date("2021-06") == datetime.date(2021, 6, 1)
    assert parse_date("2020") == datetime.date(2020, 1, 1)
    assert parse_date("invalid-date") is None
    assert parse_date("") is None
    assert parse_date(None) is None


def test_calculate_candidate_experience_years_overlapping_and_invalid():
    """Verify candidate experience calculation with overlapping jobs, ongoing roles, and invalid dates."""
    # 1. Empty / None experience -> 0.0 years
    assert calculate_candidate_experience_years(None) == 0.0
    assert calculate_candidate_experience_years([]) == 0.0

    # 2. Overlapping jobs: Job 1 (2020-01 to 2022-01 = 2 yrs), Job 2 (2021-01 to 2023-01 = 2 yrs)
    # Merged interval: 2020-01 to 2023-01 = 3.0 years (NOT 4.0 years!)
    exp_overlapping = [
        {"company": "Comp A", "title": "Dev 1", "start_date": "2020-01-01", "end_date": "2022-01-01"},
        {"company": "Comp B", "title": "Dev 2", "start_date": "2021-01-01", "end_date": "2023-01-01"},
    ]
    calc_exp = calculate_candidate_experience_years(exp_overlapping)
    assert 2.9 <= calc_exp <= 3.1

    # 3. Invalid non-empty end date: MUST SKIP interval entirely (do NOT substitute today)
    exp_invalid_end = [
        {"company": "Comp C", "title": "Dev 3", "start_date": "2020-01-01", "end_date": "InvalidDateStr"},
    ]
    assert calculate_candidate_experience_years(exp_invalid_end) == 0.0

    # 4. Invalid date range (start > end): MUST SKIP interval entirely
    exp_invalid_range = [
        {"company": "Comp D", "title": "Dev 4", "start_date": "2023-01-01", "end_date": "2020-01-01"},
    ]
    assert calculate_candidate_experience_years(exp_invalid_range) == 0.0

    # 5. Ongoing role: end_date = "Present" -> evaluates to today's date
    today = datetime.date.today()
    one_year_ago = (today - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    exp_ongoing = [
        {"company": "Comp E", "title": "Dev 5", "start_date": one_year_ago, "end_date": "Present"},
    ]
    calc_ongoing = calculate_candidate_experience_years(exp_ongoing)
    assert 0.95 <= calc_ongoing <= 1.05


def test_extract_job_required_experience_precedence_and_false_positives():
    """Verify job experience extraction precedence, false-positive suppression, and keyword fallbacks."""
    # 1. Explicit numeric in title
    assert extract_job_required_experience("AI Engineer (3+ years exp)", None) == 3.0
    assert extract_job_required_experience("Machine Learning Developer 2-4 yrs", None) == 2.0

    # 2. False-positive suppression ($100k, 5 days a week, Python 3.10, 24/7)
    fp_text = "Salary $100k - $120k. Work 5 days a week using Python 3.10 with 24/7 support. Requires 4 years of experience."
    assert extract_job_required_experience("Software Engineer", fp_text) == 4.0

    # 3. CONFLICT RESOLUTION: Explicit numeric requirement in description OVERRIDES title seniority keyword
    # "Senior AI Engineer" (senior default = 5.0) with description "Requires 2 years experience" -> MUST resolve to 2.0!
    conflict_desc = "Looking for an engineer with minimum 2 years of experience."
    assert extract_job_required_experience("Senior AI Engineer", conflict_desc) == 2.0

    # 4. Seniority keyword fallback (ONLY when no numeric pattern exists anywhere)
    assert extract_job_required_experience("Senior AI Engineer", "No numeric experience mentioned.") == 5.0
    assert extract_job_required_experience("Junior Machine Learning Developer", "Entry level position.") == 0.0

    # 5. Ambiguous / unstated experience -> None
    assert extract_job_required_experience("Software Developer", "Great company culture, apply now.") is None


def test_evaluate_experience_gap_thresholds():
    """Verify experience gap rule outcomes for a 1-year candidate across required experience levels."""
    service = DeterministicFilterService(config=FilterConfig(max_allowed_experience_gap=2.0))

    # 1-yr candidate vs 1 yr required -> PASS (gap = 0.0) -> EXP_MATCH_EXACT
    res_1 = service.evaluate_experience(candidate_exp=1.0, job_min_exp=1.0)
    assert res_1.status == "pass"
    assert res_1.reason_code == "EXP_MATCH_EXACT"

    # 1-yr candidate vs 2 yrs required -> PASS (gap = 1.0 <= 1.0) -> EXP_GAP_ACCEPTABLE
    res_2 = service.evaluate_experience(candidate_exp=1.0, job_min_exp=2.0)
    assert res_2.status == "pass"
    assert res_2.reason_code == "EXP_GAP_ACCEPTABLE"

    # 1-yr candidate vs 3 yrs required -> REVIEW (gap = 2.0, 1.0 < gap <= 2.0) -> EXP_GAP_ACCEPTABLE
    res_3 = service.evaluate_experience(candidate_exp=1.0, job_min_exp=3.0)
    assert res_3.status == "review"
    assert res_3.reason_code == "EXP_GAP_ACCEPTABLE"

    # 1-yr candidate vs 4 yrs required -> REJECT (gap = 3.0 > 2.0) -> EXP_GAP_TOO_LARGE
    res_4 = service.evaluate_experience(candidate_exp=1.0, job_min_exp=4.0)
    assert res_4.status == "reject"
    assert res_4.reason_code == "EXP_GAP_TOO_LARGE"

    # 1-yr candidate vs unspecified job experience -> REVIEW -> EXP_REQUIREMENT_UNSPECIFIED
    res_unspecified = service.evaluate_experience(candidate_exp=1.0, job_min_exp=None)
    assert res_unspecified.status == "review"
    assert res_unspecified.reason_code == "EXP_REQUIREMENT_UNSPECIFIED"


def test_evaluate_role_and_synonyms():
    """Verify target title matching, synonym clusters, partial overlap, and mismatch."""
    service = DeterministicFilterService()

    # Exact or synonym match
    res_syn = service.evaluate_role(target_titles=["AI Engineer"], job_title="Machine Learning Engineer")
    assert res_syn.status == "pass"
    assert res_syn.reason_code == "ROLE_EXACT_OR_SYNONYM"

    # Partial word overlap
    res_partial = service.evaluate_role(target_titles=["AI Engineer"], job_title="Systems Engineer")
    assert res_partial.status == "review"
    assert res_partial.reason_code == "ROLE_PARTIAL_MATCH"

    # Strict domain mismatch
    res_mismatch = service.evaluate_role(target_titles=["AI Engineer"], job_title="Accountant")
    assert res_mismatch.status == "reject"
    assert res_mismatch.reason_code == "ROLE_MISMATCH"


def test_evaluate_job_overall_precedence():
    """Verify final status calculation and passed_deterministic boolean values."""
    service = DeterministicFilterService()

    cand = CandidateProfile(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        experience=[{"start_date": "2022-01-01", "end_date": "2023-01-01"}],  # 1 yr exp
        target_titles=["AI Engineer"],
        skills=["Python", "PyTorch"],
    )

    # 1. Shortlisted Job (1 yr exp required, title matches, remote)
    job_shortlist = Job(
        id=uuid.uuid4(),
        source="manual",
        external_id="ext_1",
        title="AI Engineer (1 yr exp)",
        company="Company A",
        description_raw="Requires 1 year experience.",
        is_remote=True,
        skills_required=["Python"],
    )
    res_shortlist = service.evaluate_job(cand, job_shortlist)
    assert res_shortlist.overall_status == "shortlisted"
    assert res_shortlist.passed_deterministic is True

    # 2. Review Job (3 yrs exp required -> gap = 2.0 yrs -> REVIEW)
    job_review = Job(
        id=uuid.uuid4(),
        source="manual",
        external_id="ext_2",
        title="AI Engineer",
        company="Company B",
        description_raw="Requires 3 years of experience.",
        is_remote=True,
        skills_required=["Python"],
    )
    res_review = service.evaluate_job(cand, job_review)
    assert res_review.overall_status == "review"
    assert res_review.passed_deterministic is True  # passed_deterministic is TRUE for REVIEW

    # 3. Rejected Job (5 yrs exp required -> gap = 4.0 yrs -> REJECTED)
    job_reject = Job(
        id=uuid.uuid4(),
        source="manual",
        external_id="ext_3",
        title="AI Engineer",
        company="Company C",
        description_raw="Requires 5 years of experience.",
        is_remote=True,
        skills_required=["Python"],
    )
    res_reject = service.evaluate_job(cand, job_reject)
    assert res_reject.overall_status == "rejected"
    assert res_reject.passed_deterministic is False  # passed_deterministic is FALSE for REJECTED
