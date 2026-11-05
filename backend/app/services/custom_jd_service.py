"""
Custom External JD Tailoring & Recruiter Audit Service.
Implements:
1. Smart Raw JD Parsing (Auto-extracts Title, Company, Requirements).
2. Recruiter & ATS Gap Audit (ATS Score out of 10, Shortlist Odds, 3-column Gap Table, 6-second Cliché/Red Flag Scan).
3. The Recruiter-Friendly Rewrite (Strict Action+Result structure, anti-plagiarism, contextual skill blending, 1-page budget).
4. The 4-Line Hiring Manager Cold Outreach Generator.
5. Recruiter Coach Feedback in authentic Hinglish or English.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Any

from app.core.archetypes import classify_job_archetype
from app.schemas.ats_resume import ATSTailoredResume
from app.schemas.candidate_facts import CandidateFact, CandidateTruthVault, FactCategory
from app.schemas.tailoring import (
    ColdOutreachMessage,
    ConfirmedSkillEntry,
    CustomJDTailoringRequest,
    CustomJDTailoringResponse,
    MissingSkillPromptItem,
    PreTailoringAuditRequest,
    PreTailoringAuditResponse,
    RecruiterAuditGapItem,
    RecruiterAuditResult,
)
from app.services.fact_selector import FactSelectorEngine
from app.services.fact_verifier import COMMON_TECH_CATALOG

logger = logging.getLogger(__name__)

# Common fresher and generic filler clichés that elite recruiters skip
FRESHER_CLICHES = [
    r"\bfast learner\b",
    r"\bquick learner\b",
    r"\bhard worker\b",
    r"\bhardworking\b",
    r"\bworks? well under pressure\b",
    r"\btakes? ownership end[- ]to[- ]end\b",
    r"\bpassionate (developer|engineer|coder)\b",
    r"\bteam player\b",
    r"\bself[- ]motivated\b",
    r"\bdetail[- ]oriented\b",
    r"\bgo[- ]getter\b",
    r"\bsynergy\b",
]

# Action verbs mapped to tech domains for recommendation injection
ACTION_VERB_CATALOG = {
    "kubernetes": "Orchestrated, Provisioned, Automated, Scaled",
    "docker": "Containerized, Streamlined, Packaged, Deployed",
    "fastapi": "Engineered, Architected, Optimized, Exposed",
    "python": "Engineered, Refactored, Accelerated, Scaled",
    "pytorch": "Trained, Fine-tuned, Evaluated, Quantized",
    "postgresql": "Indexed, Queried, Modeled, Migrated",
    "redis": "Cached, Decoupled, Accelerated, Monitored",
    "aws": "Provisioned, Configured, Hardened, Monitored",
    "rag": "Embedded, Retrieved, Ranked, Benchmarked",
}


class CustomJDTailoringService:
    """Service providing end-to-end Recruiter-grade tailoring and audit for external JDs."""

    @staticmethod
    def smart_extract_job_details(
        raw_text: str,
        provided_title: Optional[str] = None,
        provided_company: Optional[str] = None,
    ) -> Tuple[str, str, List[str]]:
        """
        Extracts Job Title, Company Name, and Required Skills from raw pasted text.
        Prefers user-provided title/company if explicitly passed.
        """
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        # 1. Job Title Extraction
        extracted_title = provided_title
        if not extracted_title and lines:
            # Common patterns: "Staff AI Engineer", "Title: Machine Learning Engineer", "Role: Senior Backend"
            for line in lines[:8]:
                # Check for explicit label
                label_match = re.search(r"^(?:job\s+title|role|position|title)\s*[:\-]\s*(.+)$", line, re.I)
                if label_match:
                    extracted_title = label_match.group(1).strip()
                    break

                # Regex for common engineering roles
                role_match = re.search(
                    r"\b((?:Senior|Lead|Staff|Principal|Junior|Senior\s+Staff)?\s*(?:AI|ML|Machine\s+Learning|Software|Backend|Frontend|Full[\s-]Stack|Platform|DevOps|Data|Systems)\s*(?:Engineer|Developer|Scientist|Architect))\b",
                    line,
                    re.I,
                )
                if role_match:
                    extracted_title = role_match.group(1).strip()
                    break

            if not extracted_title and lines:
                extracted_title = lines[0][:60]  # Fallback to first line snippet

        final_title = extracted_title or "Senior Software Engineer"

        # 2. Company Name Extraction
        extracted_company = provided_company
        if not extracted_company and lines:
            for line in lines[:10]:
                comp_label = re.search(r"^(?:company|organization|employer)\s*[:\-]\s*(.+)$", line, re.I)
                if comp_label:
                    extracted_company = comp_label.group(1).strip()
                    break
                at_comp = re.search(r"\b(?:at|join|with)\s+([A-Z][A-Za-z0-9\s&]{2,25})(?:\s+is|\s+team|\.|\n|$)", line)
                if at_comp:
                    candidate_comp = at_comp.group(1).strip()
                    if candidate_comp.lower() not in {"our", "the", "a", "an", "this"}:
                        extracted_company = candidate_comp
                        break

        final_company = extracted_company or "Target Company"

        # 3. Technical Requirements Extraction
        text_lower = raw_text.lower()
        skills_found: List[str] = []
        for tech in COMMON_TECH_CATALOG:
            pattern = r"\b" + re.escape(tech) + r"\b"
            if re.search(pattern, text_lower):
                skills_found.append(tech.title())

        # Deduplicate and sort
        skills_found = sorted(list(set(skills_found)))

        return final_title, final_company, skills_found

    @staticmethod
    def generate_pre_tailoring_interview(
        vault: CandidateTruthVault,
        raw_text: Optional[str] = None,
        provided_title: Optional[str] = None,
        provided_company: Optional[str] = None,
        request: Optional[PreTailoringAuditRequest] = None,
    ) -> PreTailoringAuditResponse:
        """
        Analyzes the target JD against candidate truth vault before tailoring.
        Identifies missing skills and prepares interactive interview questions so the candidate
        can legitimately confirm hands-on knowledge without hallucination.
        """
        if request is not None:
            raw_text = request.job_description
            provided_title = request.job_title
            provided_company = request.company_name
        raw_text = raw_text or ""

        target_title, target_company, skills_found = CustomJDTailoringService.smart_extract_job_details(
            raw_text=raw_text,
            provided_title=provided_title,
            provided_company=provided_company,
        )

        candidate_skills_lower = set()
        for cat_skills in (vault.skills_inventory or {}).values():
            for s in cat_skills:
                candidate_skills_lower.add(s.lower().strip())

        matched_skills: List[str] = []
        missing_skills_items: List[MissingSkillPromptItem] = []

        for skill in skills_found:
            s_clean = skill.lower().strip()
            if s_clean in candidate_skills_lower:
                matched_skills.append(skill)
            else:
                q = f"Kya aapne '{skill}' par kisi personal project, academic work, ya internship mein kaam kiya hai?"
                proof = f"e.g. Built or integrated {skill} for data pipelines, API services, or automation."
                missing_skills_items.append(
                    MissingSkillPromptItem(
                        skill_name=skill,
                        sample_question=q,
                        example_proof=proof,
                    )
                )

        if missing_skills_items:
            miss_names = ", ".join([m.skill_name for m in missing_skills_items[:5]])
            interview_prompt = (
                f"Maine aapki target Job Description analyze ki aur dekha ki {target_company} ke {target_title} role ke liye JD me yeh skills demanded hain jo aapke profile me list nahi hain: "
                f"[{miss_names}]. Kya aapne inme se kisi par kaam kiya hai? "
                "Agar haan, toh select karein aur 1-line note batayein taaki hum bina kisi jhooth ke inhe legally aapke resume me tailor kar sakein!"
            )
        else:
            interview_prompt = f"Zabardast! {target_company} ke {target_title} role ke saare primary skills aapke profile me match ho rahe hain. Resume directly tailor karne ke liye ready hai."

        return PreTailoringAuditResponse(
            job_title=target_title,
            company_name=target_company,
            matched_skills=matched_skills,
            missing_skills=missing_skills_items,
            interview_prompt=interview_prompt,
        )

    @staticmethod
    def merge_confirmed_skills(
        vault: CandidateTruthVault,
        confirmed_skills: List[ConfirmedSkillEntry],
    ) -> CandidateTruthVault:
        """
        Dynamically merges candidate-confirmed skills into the truth vault with user consent.
        Prevents hallucination by strictly recording candidate's explicit confirmation with zero fabricated metrics.
        """
        if not confirmed_skills:
            return vault

        inventory = vault.skills_inventory or {}
        additional_skills = inventory.setdefault("Candidate Confirmed Skills", [])

        for entry in confirmed_skills:
            if not getattr(entry, "known", True):
                continue
            s_name = (entry.skill_name or "").strip()
            if not s_name:
                continue
            if s_name not in additional_skills:
                additional_skills.append(s_name)

            clean_id = re.sub(r"[^a-zA-Z0-9_]", "_", s_name.lower())
            fact_id = f"confirmed_skill_{clean_id}"
            if not any(f.fact_id == fact_id for f in (vault.facts or [])):
                note = entry.user_experience_note.strip()
                phrasing = (
                    f"Applied {s_name} in engineering workflows: {note}."
                    if note
                    else f"Hands-on engineering application with {s_name}."
                )
                vault.facts.append(
                    CandidateFact(
                        fact_id=fact_id,
                        category=FactCategory.SKILL,
                        entity_name=f"Verified Competency: {s_name}",
                        tags=[s_name.lower()],
                        metrics=[],  # Strictly ZERO fabricated metrics
                        phrasings={
                            "default": phrasing,
                            "genai": phrasing,
                            "swe": phrasing,
                        },
                        is_flagship=False,
                    )
                )

        return vault

    @staticmethod
    def perform_recruiter_audit(
        vault: CandidateTruthVault,
        target_title: str,
        target_company: str,
        jd_text: str,
        skills_required: List[str],
        language_tone: str = "hinglish",
    ) -> RecruiterAuditResult:
        """
        Executes the Recruiter & ATS Gap Audit:
        - Strict ATS Score (out of 10) and Shortlist Odds
        - 3-column Gap Finder Table (Missing Tech, Missing Verbs, Action Item)
        - 6-second Recruiter Red Flag Scan (Clichés, Vague claims, Metrics)
        - Actionable Suggestions and Coaching Critique
        """
        # 1. Collect candidate verified skills from skills_inventory & facts
        candidate_skills_lower = set()
        candidate_skills_list = []
        for cat_skills in (vault.skills_inventory or {}).values():
            for s in cat_skills:
                candidate_skills_lower.add(s.lower().strip())
                candidate_skills_list.append(s)

        fact_text_parts = []
        for f in (vault.facts or []):
            fact_text_parts.append(f.entity_name)
            fact_text_parts.extend(f.tags or [])
            for p_text in f.phrasings.values():
                fact_text_parts.append(p_text)

        full_candidate_text = " ".join([
            vault.headline or "",
            " ".join(candidate_skills_list),
            " ".join(fact_text_parts),
        ]).lower()

        # 2. Compute Skill Match and Missing Skills
        matched_skills: List[str] = []
        missing_skills: List[str] = []

        for req in skills_required:
            req_clean = req.lower().strip()
            if req_clean in candidate_skills_lower or req_clean in full_candidate_text:
                matched_skills.append(req)
            else:
                missing_skills.append(req)

        # Strict ATS Score Calculation (Out of 10)
        total_reqs = max(1, len(skills_required))
        match_ratio = len(matched_skills) / total_reqs
        base_score = 4.0 + (match_ratio * 5.5)  # Scale between 4.0 and 9.5
        ats_score = round(min(9.8, max(3.5, base_score)), 1)

        # Shortlist Probability
        if ats_score >= 7.8:
            shortlist_chance = "High"
        elif ats_score >= 5.5:
            shortlist_chance = "Medium"
        else:
            shortlist_chance = "Low"

        # 3. Build 3-Column Gap Finder Table
        gap_table: List[RecruiterAuditGapItem] = []
        for miss in missing_skills[:6]:
            miss_lower = miss.lower()
            verbs = ACTION_VERB_CATALOG.get(miss_lower, "Engineered, Architected, Automated, Benchmarked")

            if "kubernetes" in miss_lower:
                action = "Blend your production Docker and container deployment experience to contextually demonstrate orchestration readiness without falsifying k8s cluster admin."
            elif "aws" in miss_lower or "cloud" in miss_lower:
                action = "Highlight your FastAPI containerized cloud deployments and API gateway routing to bridge cloud infrastructure requirements."
            elif "pytorch" in miss_lower or "tensorflow" in miss_lower:
                action = "Highlight your RAG vector indexing and embedding evaluation pipelines using sentence-transformers to showcase ML depth."
            else:
                action = f"Contextually position adjacent backend systems experience using action verbs like '{verbs.split(',')[0]}' to address {miss}."

            gap_table.append(
                RecruiterAuditGapItem(
                    missing_tech=miss,
                    missing_action_verbs=verbs,
                    recommended_action=action,
                )
            )

        # 4. Recruiter 6-Second Red Flag Scan (Clichés & Missing Metrics)
        red_flags: List[str] = []
        hard_truths: List[str] = []

        # Check for fresher filler clichés in candidate text
        for cliche_pat in FRESHER_CLICHES:
            match = re.search(cliche_pat, full_candidate_text, re.I)
            if match:
                cliche_word = match.group(0)
                red_flags.append(f"Cliché Detected: Remove generic filler phrase '{cliche_word}' — corporate technical recruiters skip resumes with self-praising adjectives.")

        # Check for metrics & numbers
        has_metrics = bool(re.search(r"\b(?:\d+(?:\.\d+)?(?:%|[kmgbKMGB]+))\b", full_candidate_text))
        if not has_metrics:
            red_flags.append("Missing Quantifiable Metrics: Your bullet points lack numerical impact (%, latency ms, scale). A 6-second scan requires measurable results.")

        # Hard Truths
        if missing_skills:
            hard_truths.append(f"Primary Recruiter Risk: The JD explicitly prioritizes {', '.join(missing_skills[:3])}, which are not in your verified profile.")
        if shortlist_chance == "Medium":
            hard_truths.append("Recruiters with 100+ applicants will prioritize candidates with direct title and stack overlap unless you immediately highlight your flagship technical projects.")
        elif shortlist_chance == "Low":
            hard_truths.append("High pivot gap: Your verified background requires strong transferable positioning to avoid automatic ATS filtering.")
        else:
            hard_truths.append("Strong technical alignment: Your core stack matches the role. The primary hurdle is keeping formatting strictly single-page with zero fluff.")

        # 5. Actionable Suggestions
        actionable_suggestions = [
            f"Front-load verified power tools ({', '.join(matched_skills[:4])}) in your Summary and Skills categories.",
            "Enforce strict Action + Result bullet structure (e.g. 'Engineered [System] achieving [X% Metric]').",
            "Keep the resume strictly within the 42-line 1-page budget — never leak onto a second page.",
        ]
        if missing_skills:
            actionable_suggestions.append(f"In your interview and cover letter, transparently acknowledge {missing_skills[0]} while anchoring on your verified adjacent strengths.")

        # 6. Recruiter Notes (Structured 4-Section Hinglish/English Evaluation)
        gap_summary = "\n".join([f"   - **{m.missing_tech}**: Missing in profile. Recommended action: {m.recommended_action}" for m in gap_table[:4]]) or "   - No critical technical skills missing."
        truths_summary = "\n".join([f"   - {ht}" for ht in hard_truths])
        actions_summary = "\n".join([f"   - {act}" for act in actionable_suggestions])

        if language_tone.lower() == "hinglish":
            critique = (
                f"### 🎯 Elite Technical Recruiter & ATS Scanner Review\n\n"
                f"1. **ATS Score & Selection Chances**:\n"
                f"   - **Score**: {ats_score} / 10\n"
                f"   - **Shortlist Likelihood**: **{shortlist_chance}** ({target_company} — {target_title})\n\n"
                f"2. **Skill Gap Analysis (Missing Elements)**:\n"
                f"{gap_summary}\n\n"
                f"3. **Hard Truths (Why I might get rejected)**:\n"
                f"{truths_summary}\n\n"
                f"4. **Actionable Suggestions (Exact Rewrites)**:\n"
                f"{actions_summary}\n\n"
                f"> **Recruiter Note**: Resume ko 1-page strict layout par lock kiya gaya hai. Humne ungrounded buzzwords hata kar Action + Result metrics front-load kar diye hain."
            )
        else:
            critique = (
                f"### 🎯 Elite Technical Recruiter & ATS Scanner Review\n\n"
                f"1. **ATS Score & Selection Chances**:\n"
                f"   - **Score**: {ats_score} / 10\n"
                f"   - **Shortlist Likelihood**: **{shortlist_chance}** ({target_company} — {target_title})\n\n"
                f"2. **Skill Gap Analysis (Missing Elements)**:\n"
                f"{gap_summary}\n\n"
                f"3. **Hard Truths (Why I might get rejected)**:\n"
                f"{truths_summary}\n\n"
                f"4. **Actionable Suggestions (Exact Rewrites)**:\n"
                f"{actions_summary}\n"
            )

        return RecruiterAuditResult(
            ats_score=ats_score,
            shortlist_chance=shortlist_chance,
            gap_table=gap_table,
            hard_truths=hard_truths,
            red_flags=red_flags,
            actionable_suggestions=actionable_suggestions,
            recruiter_notes=critique,
        )

    @staticmethod
    def generate_cold_outreach(
        vault: CandidateTruthVault,
        target_title: str,
        target_company: str,
        jd_text: str,
    ) -> ColdOutreachMessage:
        """
        Generates a crisp 4-line LinkedIn / Email cold outreach for the hiring manager.
        Tone: Confident, specific, zero desperation.
        """
        cand_name = vault.candidate_name or "Candidate"
        top_project = "production systems"
        if vault.facts:
            flagships = [f.entity_name for f in vault.facts if f.is_flagship]
            top_project = flagships[0] if flagships else vault.facts[0].entity_name

        all_skills = [s for sublist in (vault.skills_inventory or {}).values() for s in sublist]
        top_skills = ", ".join(all_skills[:3]) if all_skills else "distributed backend systems"

        subject = f"Quick question regarding {target_title} role at {target_company}"
        body = (
            f"Hi {target_company} Hiring Team,\n\n"
            f"1. I noticed {target_company} is expanding its {target_title} capabilities, particularly around high-throughput architectures.\n"
            f"2. In my recent work on {top_project}, I engineered scalable systems using {top_skills}, optimizing retrieval latency and throughput.\n"
            f"3. Having reviewed your team's mission, I believe my background in production-grade reliability aligns directly with your current priorities.\n"
            f"4. Are you open to a brief 10-minute sync this Thursday or Friday to discuss how I can contribute immediately?"
        )

        return ColdOutreachMessage(
            subject=subject,
            body=body,
            target_platform="LinkedIn",
        )

    @staticmethod
    def tailor_custom_jd(
        vault: CandidateTruthVault,
        request: CustomJDTailoringRequest,
    ) -> CustomJDTailoringResponse:
        """
        End-to-end execution:
        1. Auto-extracts details from raw JD.
        2. Assembles 1-page ATSTailoredResume strictly derived from verified candidate profile.
        3. Executes Pre-Flight Recruiter & ATS Gap Audit.
        4. Generates 4-line Cold Outreach.
        5. Assembles response bundle.
        """
        # 1. Smart Extraction
        target_title, target_company, skills_found = CustomJDTailoringService.smart_extract_job_details(
            raw_text=request.job_description,
            provided_title=request.job_title,
            provided_company=request.company_name,
        )

        # Merge candidate confirmed missing skills if provided
        confirmed = getattr(request, "confirmed_skills", None)
        if confirmed:
            vault = CustomJDTailoringService.merge_confirmed_skills(vault, confirmed)

        # 2. Assemble 1-Page ATS Resume via FactSelectorEngine
        tailored_resume: ATSTailoredResume = FactSelectorEngine.assemble_tailored_resume(
            vault=vault,
            job_title=target_title,
            job_company=target_company,
            job_description=request.job_description,
            skills_required=skills_found,
            forced_archetype_id=request.archetype_id,
        )

        # 3. Recruiter & ATS Gap Audit
        recruiter_audit = CustomJDTailoringService.perform_recruiter_audit(
            vault=vault,
            target_title=target_title,
            target_company=target_company,
            jd_text=request.job_description,
            skills_required=skills_found,
            language_tone=request.language_tone or "hinglish",
        )

        # 4. Cold Outreach Message
        cold_outreach = CustomJDTailoringService.generate_cold_outreach(
            vault=vault,
            target_title=target_title,
            target_company=target_company,
            jd_text=request.job_description,
        )

        # 5. Tailored Cover Letter
        skills_summary = ", ".join([s for sublist in (vault.skills_inventory or {}).values() for s in sublist][:4]) or "scalable engineering"
        project_ref = vault.facts[0].entity_name if vault.facts else "production cloud platforms"
        cover_letter = (
            f"Dear Hiring Team at {target_company},\n\n"
            f"I am writing to express my strong enthusiasm for the {target_title} position. "
            f"With verified hands-on expertise spanning {skills_summary}, "
            f"I have consistently engineered robust, production-grade solutions designed for measurable impact.\n\n"
            f"In my work on {project_ref}, "
            f"I focused on architectural elegance and high-throughput reliability. "
            f"I am energized by {target_company}'s engineering challenges and look forward to discussing how my experience can support your team's mission.\n\n"
            f"Sincerely,\n{vault.candidate_name}"
        )

        return CustomJDTailoringResponse(
            job_title=target_title,
            company_name=target_company,
            tailored_resume=tailored_resume.model_dump(),
            cover_letter=cover_letter,
            recruiter_audit=recruiter_audit,
            cold_outreach=cold_outreach,
            job_id=None,
        )
