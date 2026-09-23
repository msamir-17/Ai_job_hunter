from typing import Any
from app.models import CandidateProfile
from app.schemas.resume import EducationItem, ExperienceItem, ResumeDraft


def merge_skills(
    existing_skills: list[str] | None,
    confirmed_skills: list[str] | None,
) -> list[str]:
    """
    Merge existing verified skills with newly confirmed draft skills.

    Performs case-insensitive deduplication while preserving canonical casing
    (preferring existing casing when present).
    """
    existing = existing_skills or []
    confirmed = confirmed_skills or []

    seen_map: dict[str, str] = {}

    for s in existing:
        if isinstance(s, str) and s.strip():
            key = s.strip().lower()
            if key not in seen_map:
                seen_map[key] = s.strip()

    for s in confirmed:
        if isinstance(s, str) and s.strip():
            key = s.strip().lower()
            if key not in seen_map:
                seen_map[key] = s.strip()

    return list(seen_map.values())


def merge_target_titles(
    existing_titles: list[str] | None,
    confirmed_titles: list[str] | None,
) -> list[str]:
    """
    Merge existing target titles with newly confirmed target titles.

    Performs case-insensitive deduplication while preserving canonical casing.
    """
    existing = existing_titles or []
    confirmed = confirmed_titles or []

    seen_map: dict[str, str] = {}

    for t in existing:
        if isinstance(t, str) and t.strip():
            key = t.strip().lower()
            if key not in seen_map:
                seen_map[key] = t.strip()

    for t in confirmed:
        if isinstance(t, str) and t.strip():
            key = t.strip().lower()
            if key not in seen_map:
                seen_map[key] = t.strip()

    return list(seen_map.values())


def merge_experience(
    existing_exp: list[dict[str, Any]] | None,
    confirmed_exp: list[ExperienceItem] | list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """
    Merge existing verified experience entries with confirmed experience entries.

    MVP LIMITATION DOCUMENTATION:
    Experience items are identified deterministically by the composite key:
    `(company.strip().lower(), title.strip().lower())`.
    If a candidate held multiple distinct roles at the exact same company with the exact
    same title, they will be merged into a single entry under this MVP key.

    - Preserves all existing experience entries.
    - Updates non-null fields on matching entries.
    - Appends genuinely new experience entries.
    """
    result_entries: list[dict[str, Any]] = [dict(item) for item in (existing_exp or [])]

    raw_confirmed = confirmed_exp or []
    confirmed_dicts: list[dict[str, Any]] = []
    for item in raw_confirmed:
        if isinstance(item, ExperienceItem):
            confirmed_dicts.append(item.model_dump())
        elif isinstance(item, dict):
            confirmed_dicts.append(dict(item))

    for conf_item in confirmed_dicts:
        c_company = (conf_item.get("company") or "").strip().lower()
        c_title = (conf_item.get("title") or "").strip().lower()

        # If both company and title are missing, treat as distinct entry
        if not c_company and not c_title:
            result_entries.append(conf_item)
            continue

        matched_index = None
        for idx, exist_item in enumerate(result_entries):
            e_company = (exist_item.get("company") or "").strip().lower()
            e_title = (exist_item.get("title") or "").strip().lower()
            if e_company == c_company and e_title == c_title:
                matched_index = idx
                break

        if matched_index is not None:
            # Update matching entry with non-null confirmed values (preserving existing canonical company/title casing)
            target = result_entries[matched_index]
            for key, val in conf_item.items():
                if key in ("company", "title") and target.get(key):
                    continue
                if val is not None and val != [] and val != "":
                    target[key] = val
        else:
            result_entries.append(conf_item)

    return result_entries


def merge_education(
    existing_edu: list[dict[str, Any]] | None,
    confirmed_edu: list[EducationItem] | list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """
    Merge existing verified education entries with confirmed education entries.

    MVP LIMITATION DOCUMENTATION:
    Education items are identified deterministically by the composite key:
    `(institution.strip().lower(), degree.strip().lower(), field_of_study.strip().lower())`.

    - Preserves all existing education entries.
    - Updates non-null fields on matching entries.
    - Appends new education entries.
    """
    result_entries: list[dict[str, Any]] = [dict(item) for item in (existing_edu or [])]

    raw_confirmed = confirmed_edu or []
    confirmed_dicts: list[dict[str, Any]] = []
    for item in raw_confirmed:
        if isinstance(item, EducationItem):
            confirmed_dicts.append(item.model_dump())
        elif isinstance(item, dict):
            confirmed_dicts.append(dict(item))

    for conf_item in confirmed_dicts:
        c_inst = (conf_item.get("institution") or "").strip().lower()
        c_deg = (conf_item.get("degree") or "").strip().lower()
        c_field = (conf_item.get("field_of_study") or "").strip().lower()

        if not c_inst and not c_deg and not c_field:
            result_entries.append(conf_item)
            continue

        matched_index = None
        for idx, exist_item in enumerate(result_entries):
            e_inst = (exist_item.get("institution") or "").strip().lower()
            e_deg = (exist_item.get("degree") or "").strip().lower()
            e_field = (exist_item.get("field_of_study") or "").strip().lower()
            if e_inst == c_inst and e_deg == c_deg and e_field == c_field:
                matched_index = idx
                break

        if matched_index is not None:
            target = result_entries[matched_index]
            for key, val in conf_item.items():
                if key in ("institution", "degree", "field_of_study") and target.get(key):
                    continue
                if val is not None and val != [] and val != "":
                    target[key] = val
        else:
            result_entries.append(conf_item)

    return result_entries


def merge_draft_into_candidate_profile(
    profile: CandidateProfile,
    draft: ResumeDraft,
) -> CandidateProfile:
    """
    Merge a user-confirmed ResumeDraft into a CandidateProfile entity.

    Enforces CandidateProfile preservation rules:
    - Merges skills and target titles with case-insensitive deduplication.
    - Merges experience and education without deleting pre-existing entries.
    - Updates headline/summary if non-null values are explicitly confirmed.
    """
    # 1. Merge skills
    profile.skills = merge_skills(profile.skills, draft.skills)

    # 2. Merge target titles
    profile.target_titles = merge_target_titles(profile.target_titles, draft.target_titles)

    # 3. Merge experience
    profile.experience = merge_experience(profile.experience, draft.experience)

    # 4. Merge education
    profile.education = merge_education(profile.education, draft.education)

    # 5. Headline update (presentation field)
    if draft.headline is not None and draft.headline.strip():
        profile.headline = draft.headline.strip()

    # 6. Summary update (presentation field)
    if draft.summary is not None and draft.summary.strip():
        profile.summary = draft.summary.strip()

    return profile
