"""
Fact Selector and One-Page Line Budget Engine.
Selects candidate facts, projects, and angle-specific approved phrasings based on
the job description and active archetype lens, strictly budgeting content for 1-page ATS compliance.
"""
import math
from typing import Dict, List, Optional
from app.core.archetypes import classify_job_archetype, get_archetype
from app.schemas.archetype import ArchetypeConfig
from app.schemas.ats_resume import ATSTailoredResume, OnePageBudgetAudit, TailoredProjectItem
from app.schemas.candidate_facts import CandidateFact, CandidateTruthVault


class FactSelectorEngine:
    """
    Engine that selects, orders, and formats candidate facts for single-page ATS-ready resumes.
    Never fabricates or freely hallucinates text; exclusively selects pre-approved angle phrasings.
    """

    @staticmethod
    def audit_one_page_budget(
        summary_text: str,
        skill_categories: Dict[str, List[str]],
        projects: List[TailoredProjectItem],
        education_lines: List[str],
    ) -> OnePageBudgetAudit:
        """
        Estimate line count across all resume sections and verify single-page compliance.
        Standard ATS page budget is 40-42 total lines (~450-500 words).
        """
        chars_per_line = 90  # Average characters per line in standard 10pt ATS single-column layout

        # Header + Contact Info: ~3 lines
        header_lines = 3

        # Summary lines
        summary_lines = max(2, math.ceil(len(summary_text) / chars_per_line)) + 1  # +1 for section heading

        # Skills lines: Section header + 1 line per displayed category
        skills_lines = 1 + len(skill_categories)

        # Projects lines: Section header + (Project title + bullets)
        projects_lines = 1
        for p in projects:
            projects_lines += 1  # Project title & role line
            for b in p.bullets:
                bullet_lines = max(1, math.ceil(len(b) / chars_per_line))
                projects_lines += bullet_lines

        # Education lines: Section header + items
        education_lines_count = 1 + len(education_lines)

        total_lines = header_lines + summary_lines + skills_lines + projects_lines + education_lines_count
        total_chars = (
            len(summary_text)
            + sum(len(cat) + sum(len(s) for s in skills) for cat, skills in skill_categories.items())
            + sum(sum(len(b) for b in p.bullets) for p in projects)
            + sum(len(e) for e in education_lines)
        )

        is_one_page = total_lines <= 42
        notes = (
            "Strictly 1-page compliant."
            if is_one_page
            else f"Exceeds 1-page budget by {total_lines - 42} lines. Auto-trimmed lower priority bullets."
        )

        return OnePageBudgetAudit(
            total_characters=total_chars,
            estimated_total_lines=total_lines,
            max_allowed_lines=42,
            is_strictly_one_page=is_one_page,
            summary_lines=summary_lines,
            skills_lines=skills_lines,
            projects_lines=projects_lines,
            education_lines=education_lines_count,
            audit_notes=notes,
        )

    @classmethod
    def assemble_tailored_resume(
        cls,
        vault: CandidateTruthVault,
        job_title: str,
        job_company: str,
        job_description: str,
        skills_required: Optional[List[str]] = None,
        forced_archetype_id: Optional[str] = None,
    ) -> ATSTailoredResume:
        """
        Assemble a complete ATS-ready tailored resume:
        1. Select archetype lens (user-specified or auto-classified from JD).
        2. Order skill categories according to archetype priorities.
        3. Select top projects (guaranteeing flagship project first) and pick approved phrasings.
        4. Audit one-page budget and auto-trim if necessary.
        """
        # 1. Determine Archetype
        if forced_archetype_id:
            archetype = get_archetype(forced_archetype_id)
        else:
            classification = classify_job_archetype(job_title, job_description, skills_required)
            archetype = get_archetype(classification.recommended_archetype_id)

        # 2. Formulate Headline and Summary
        headline = archetype.headline_template
        summary = archetype.summary_template

        # 3. Order Skills Categories
        ordered_skills: Dict[str, List[str]] = {}
        for cat in archetype.skill_category_order:
            if cat in vault.skills_inventory:
                ordered_skills[cat] = vault.skills_inventory[cat]
        # Include any remaining categories not explicitly in priority list
        for cat, skills in vault.skills_inventory.items():
            if cat not in ordered_skills:
                ordered_skills[cat] = skills

        # 4. Group Facts by Project and Select Phrasings
        facts_by_project: Dict[str, List[CandidateFact]] = {}
        project_meta: Dict[str, Dict] = {}

        for f in vault.facts:
            if f.category.value == "project":
                p_name = f.entity_name
                if p_name not in facts_by_project:
                    facts_by_project[p_name] = []
                    project_meta[p_name] = {
                        "role": f.role_or_title or "Engineer",
                        "timeline": f"{f.start_date or ''} - {f.end_date or ''}".strip(" -"),
                        "is_flagship": f.is_flagship,
                    }
                facts_by_project[p_name].append(f)

        # Sort projects: Flagship first, then by matching archetype tags
        sorted_project_names = sorted(
            facts_by_project.keys(),
            key=lambda name: (
                1 if project_meta[name]["is_flagship"] else 0,
                sum(
                    1
                    for fact in facts_by_project[name]
                    if archetype.primary_angle in fact.tags or any(t in fact.tags for t in ["genai", "swe", "backend"])
                ),
            ),
            reverse=True,
        )

        # Select up to max_projects
        selected_project_names = sorted_project_names[: archetype.max_projects]

        project_items: List[TailoredProjectItem] = []
        for name in selected_project_names:
            meta = project_meta[name]
            is_flagship = meta["is_flagship"]
            max_bullets = (
                archetype.max_bullets_per_flagship if is_flagship else archetype.max_bullets_per_standard
            )

            # Sort facts for this project: prefer facts that have this archetype angle
            p_facts = facts_by_project[name]
            sorted_facts = sorted(
                p_facts,
                key=lambda fact: (
                    1 if archetype.primary_angle in fact.phrasings else 0,
                    1 if archetype.primary_angle in fact.tags else 0,
                ),
                reverse=True,
            )

            chosen_facts = sorted_facts[:max_bullets]
            bullets: List[str] = []
            fact_ids: List[str] = []

            for fact in chosen_facts:
                fact_ids.append(fact.fact_id)
                # Pick phrasing: primary_angle -> default -> first available
                phrasing = (
                    fact.phrasings.get(archetype.primary_angle)
                    or fact.phrasings.get("default")
                    or next(iter(fact.phrasings.values()))
                )
                bullets.append(phrasing)

            project_items.append(
                TailoredProjectItem(
                    project_name=name,
                    role_or_title=meta["role"],
                    timeline=meta["timeline"],
                    is_flagship=is_flagship,
                    bullets=bullets,
                    cited_fact_ids=fact_ids,
                )
            )

        # 5. Format Education
        education_lines: List[str] = []
        for edu in vault.education:
            edu_text = edu.phrasings.get(archetype.primary_angle) or edu.phrasings.get("default") or edu.entity_name
            education_lines.append(edu_text)

        # 6. Audit One-Page Budget & Auto-Trim if required
        budget_audit = cls.audit_one_page_budget(
            summary_text=summary,
            skill_categories=ordered_skills,
            projects=project_items,
            education_lines=education_lines,
        )

        # If budget exceeded, trim 1 bullet from the last standard project
        if not budget_audit.is_strictly_one_page and len(project_items) > 1:
            for p in reversed(project_items):
                if not p.is_flagship and len(p.bullets) > 1:
                    p.bullets.pop()
                    p.cited_fact_ids.pop()
                    break

            budget_audit = cls.audit_one_page_budget(
                summary_text=summary,
                skill_categories=ordered_skills,
                projects=project_items,
                education_lines=education_lines,
            )

        return ATSTailoredResume(
            candidate_name=vault.candidate_name,
            headline=headline,
            email=vault.email,
            location=vault.location,
            github_url=vault.github_url,
            linkedin_url=vault.linkedin_url,
            portfolio_url=vault.portfolio_url,
            target_job_title=job_title,
            target_company=job_company,
            archetype_id=archetype.archetype_id,
            archetype_display_name=archetype.display_name,
            summary=summary,
            skill_categories=ordered_skills,
            projects=project_items,
            education=education_lines,
            budget_audit=budget_audit,
        )
