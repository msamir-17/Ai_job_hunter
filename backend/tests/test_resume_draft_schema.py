import pytest
from pydantic import ValidationError

from app.schemas.resume import EducationItem, ExperienceItem, ResumeDraft


class TestResumeDraftSchema:
    def test_valid_full_resume_draft(self):
        draft_data = {
            "headline": "Senior AI Engineer",
            "summary": "5+ years developing ML & GenAI applications.",
            "skills": ["Python", "FastAPI", "PyTorch", "pgvector"],
            "experience": [
                {
                    "company": "Tech Corp",
                    "title": "AI Lead",
                    "location": "Remote",
                    "start_date": "2022-01",
                    "end_date": "Present",
                    "description": "Led GenAI team",
                    "achievements": ["Built LLM app", "Reduced latency by 40%"],
                    "technologies": ["Python", "FastAPI"],
                }
            ],
            "education": [
                {
                    "institution": "State University",
                    "degree": "B.S.",
                    "field_of_study": "Computer Science",
                    "start_date": "2016",
                    "end_date": "2020",
                    "description": "Graduated with Honors",
                }
            ],
            "target_titles": ["GenAI Lead", "AI Architect"],
        }

        draft = ResumeDraft(**draft_data)
        assert draft.headline == "Senior AI Engineer"
        assert len(draft.skills) == 4
        assert len(draft.experience) == 1
        assert draft.experience[0].company == "Tech Corp"
        assert len(draft.target_titles) == 2

    def test_minimal_resume_draft_defaults(self):
        draft = ResumeDraft()
        assert draft.headline is None
        assert draft.summary is None
        assert draft.skills == []
        assert draft.experience == []
        assert draft.education == []
        assert draft.target_titles == []

    def test_experience_item_defaults(self):
        exp = ExperienceItem(company="Acme Corp")
        assert exp.company == "Acme Corp"
        assert exp.title is None
        assert exp.achievements == []
        assert exp.technologies == []

    def test_education_item_defaults(self):
        edu = EducationItem(institution="MIT")
        assert edu.institution == "MIT"
        assert edu.degree is None
        assert edu.field_of_study is None

    def test_invalid_types_raise_validation_error(self):
        with pytest.raises(ValidationError):
            ResumeDraft(skills="Not a list")  # skills must be list
