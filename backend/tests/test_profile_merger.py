from app.models import CandidateProfile
from app.schemas.resume import EducationItem, ExperienceItem, ResumeDraft
from app.services.profile_merger import (
    merge_draft_into_candidate_profile,
    merge_education,
    merge_experience,
    merge_skills,
    merge_target_titles,
)


class TestProfileMergerService:
    def test_skills_case_insensitive_deduplication(self):
        existing = ["Python", "PyTorch", "LangGraph"]
        confirmed = ["python", "PYTHON", "SQL", "PyTorch"]
        merged = merge_skills(existing, confirmed)
        assert merged == ["Python", "PyTorch", "LangGraph", "SQL"]

    def test_target_titles_case_insensitive_deduplication(self):
        existing = ["AI Engineer"]
        confirmed = ["ai engineer", "GenAI Lead"]
        merged = merge_target_titles(existing, confirmed)
        assert merged == ["AI Engineer", "GenAI Lead"]

    def test_experience_preserves_existing_and_appends_new(self):
        existing = [
            {"company": "Tech Corp", "title": "ML Engineer", "description": "Worked on NLP"}
        ]
        confirmed = [
            ExperienceItem(company="New Startup", title="Lead Engineer", description="Building GenAI app")
        ]
        merged = merge_experience(existing, confirmed)
        assert len(merged) == 2
        assert merged[0]["company"] == "Tech Corp"
        assert merged[1]["company"] == "New Startup"

    def test_experience_updates_matching_company_and_title(self):
        existing = [
            {"company": "Tech Corp", "title": "ML Engineer", "description": "Old description"}
        ]
        confirmed = [
            ExperienceItem(
                company="tech corp",
                title="ml engineer",
                description="Updated new description",
                achievements=["Reduced latency by 40%"],
            )
        ]
        merged = merge_experience(existing, confirmed)
        assert len(merged) == 1
        assert merged[0]["company"] == "Tech Corp"  # Preserves original casing
        assert merged[0]["description"] == "Updated new description"
        assert merged[0]["achievements"] == ["Reduced latency by 40%"]

    def test_education_preserves_existing_and_merges_matches(self):
        existing = [
            {"institution": "MIT", "degree": "B.S.", "field_of_study": "CS"}
        ]
        confirmed = [
            EducationItem(institution="MIT", degree="B.S.", field_of_study="CS", description="Honors"),
            EducationItem(institution="Stanford", degree="M.S.", field_of_study="AI"),
        ]
        merged = merge_education(existing, confirmed)
        assert len(merged) == 2
        assert merged[0]["institution"] == "MIT"
        assert merged[0]["description"] == "Honors"
        assert merged[1]["institution"] == "Stanford"

    def test_full_profile_merge_headline_and_summary(self):
        profile = CandidateProfile(
            headline="Original Headline",
            summary="Original Summary",
            skills=["Python", "Docker"],
            target_titles=["AI Engineer"],
        )
        draft = ResumeDraft(
            headline="New Confirmed Headline",
            summary=None,  # Should preserve original summary
            skills=["FastAPI", "python"],
            target_titles=["GenAI Lead"],
        )

        merged_profile = merge_draft_into_candidate_profile(profile, draft)

        assert merged_profile.headline == "New Confirmed Headline"
        assert merged_profile.summary == "Original Summary"
        assert merged_profile.skills == ["Python", "Docker", "FastAPI"]
        assert merged_profile.target_titles == ["AI Engineer", "GenAI Lead"]
