"""
Native PDF Generation Engine for ATS-Compliant Resumes.
Uses ReportLab to generate strictly 1-page, single-column ATS resumes.
Optimized for zero external C/GTK dependencies, valid PDF metadata, and high parsing fidelity.
"""
import io
import re
from typing import List, Dict
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.schemas.ats_resume import ATSTailoredResume


def _clean_text(text: str) -> str:
    """Sanitize text for XML compatibility in ReportLab Paragraphs."""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generate_ats_resume_pdf(resume: ATSTailoredResume) -> bytes:
    """
    Render an ATSTailoredResume object into a strictly single-page, ATS-compliant binary PDF.
    
    Layout specifications:
    - Paper: Letter (8.5 x 11 inches)
    - Margins: 0.40 inch (tight ATS budget)
    - Typography: Standard Helvetica / Helvetica-Bold / Helvetica-Oblique
    - Formatting: Single-column standard structure without unparseable multi-column text frames
    """
    buffer = io.BytesIO()

    # Usable width: 8.5 * 72 - 2 * (0.40 * 72) = 612 - 57.6 = 554.4 pt
    margin = 0.40 * inch
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=margin,
        rightMargin=margin,
        topMargin=margin,
        bottomMargin=margin,
        title=f"{resume.candidate_name} - ATS Resume",
        author=resume.candidate_name,
        subject=f"Tailored Resume for {resume.target_job_title} at {resume.target_company}",
    )

    styles = getSampleStyleSheet()

    # Color Palette (Standard ATS Contrast)
    COLOR_PRIMARY = HexColor("#111827")     # Dark Slate
    COLOR_MUTED = HexColor("#4B5563")       # Slate Muted
    COLOR_BORDER = HexColor("#1F2937")      # Section Rule
    COLOR_FLAGSHIP_BG = HexColor("#E0F2FE") # Sky-100
    COLOR_FLAGSHIP_TXT = HexColor("#0369A1")# Sky-700

    # Custom Typography Styles
    style_name = ParagraphStyle(
        "CandidateName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=17,
        alignment=TA_CENTER,
        textColor=COLOR_PRIMARY,
        textTransform="uppercase",
        spaceAfter=2,
    )

    style_headline = ParagraphStyle(
        "CandidateHeadline",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.5,
        leading=12,
        alignment=TA_CENTER,
        textColor=HexColor("#374151"),
        spaceAfter=2,
    )

    style_contact = ParagraphStyle(
        "ContactBar",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.5,
        alignment=TA_CENTER,
        textColor=COLOR_MUTED,
        spaceAfter=4,
    )

    style_section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.2,
        leading=11.5,
        textColor=COLOR_PRIMARY,
        textTransform="uppercase",
        spaceBefore=5,
        spaceAfter=2,
    )

    style_body = ParagraphStyle(
        "BodyTextJustified",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=10.8,
        alignment=TA_JUSTIFY,
        textColor=COLOR_PRIMARY,
        spaceAfter=3,
    )

    style_skill_category = ParagraphStyle(
        "SkillCategory",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.2,
        leading=10.5,
        textColor=COLOR_PRIMARY,
    )

    style_skill_items = ParagraphStyle(
        "SkillItems",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.5,
        textColor=HexColor("#1F2937"),
    )

    style_project_title = ParagraphStyle(
        "ProjectTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=11,
        textColor=COLOR_PRIMARY,
    )

    style_project_timeline = ParagraphStyle(
        "ProjectTimeline",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=11,
        alignment=TA_RIGHT,
        textColor=COLOR_MUTED,
    )

    style_bullet = ParagraphStyle(
        "BulletText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.0,
        leading=10.2,
        leftIndent=11,
        firstLineIndent=-11,
        textColor=COLOR_PRIMARY,
        spaceAfter=1.5,
    )

    style_education = ParagraphStyle(
        "EducationItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.2,
        leading=10.5,
        textColor=COLOR_PRIMARY,
        spaceAfter=1.5,
    )

    story = []

    # 1. Header (Name, Headline, Contact)
    story.append(Paragraph(_clean_text(resume.candidate_name), style_name))
    story.append(Paragraph(_clean_text(resume.headline), style_headline))

    contact_parts = [_clean_text(resume.location), _clean_text(resume.email)]
    if resume.github_url:
        contact_parts.append(f"GitHub: {_clean_text(resume.github_url.replace('https://', ''))}")
    if resume.linkedin_url:
        contact_parts.append(f"LinkedIn: {_clean_text(resume.linkedin_url.replace('https://', ''))}")
    if resume.portfolio_url:
        contact_parts.append(f"Portfolio: {_clean_text(resume.portfolio_url.replace('https://', ''))}")

    story.append(Paragraph(" &bull; ".join(contact_parts), style_contact))
    story.append(HRFlowable(width="100%", thickness=0.75, color=COLOR_BORDER, spaceBefore=2, spaceAfter=4))

    # Helper function for section headings
    def add_section_header(title: str):
        story.append(Paragraph(title, style_section_title))
        story.append(HRFlowable(width="100%", thickness=0.5, color=COLOR_BORDER, spaceBefore=1, spaceAfter=3))

    # 2. Professional Summary
    if resume.summary:
        add_section_header("Professional Summary")
        story.append(Paragraph(_clean_text(resume.summary), style_body))

    # 3. Technical Skills
    if resume.skill_categories:
        add_section_header("Technical Skills")
        skill_rows = []
        for cat, skills in resume.skill_categories.items():
            cat_p = Paragraph(f"<b>{_clean_text(cat)}:</b>", style_skill_category)
            skills_p = Paragraph(_clean_text(", ".join(skills)), style_skill_items)
            skill_rows.append([cat_p, skills_p])

        if skill_rows:
            skills_table = Table(
                skill_rows,
                colWidths=[120, 434],
                spaceBefore=1,
                spaceAfter=3,
            )
            skills_table.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0.8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0.8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ])
            )
            story.append(skills_table)

    # 4. Key Projects & Systems
    if resume.projects:
        add_section_header("Key Projects & Systems")
        for proj in resume.projects:
            flagship_tag = " <b>[Flagship]</b>" if proj.is_flagship else ""
            left_text = f"<b>{_clean_text(proj.project_name)}</b> — <i>{_clean_text(proj.role_or_title)}</i>{flagship_tag}"
            right_text = _clean_text(proj.timeline)

            proj_header_table = Table(
                [[Paragraph(left_text, style_project_title), Paragraph(right_text, style_project_timeline)]],
                colWidths=[430, 124],
                spaceBefore=1.5,
                spaceAfter=1.5,
            )
            proj_header_table.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ])
            )
            story.append(proj_header_table)

            for bullet in proj.bullets:
                story.append(Paragraph(f"&bull;&nbsp; {_clean_text(bullet)}", style_bullet))

    # 5. Education
    if resume.education:
        add_section_header("Education")
        for edu in resume.education:
            story.append(Paragraph(f"&bull;&nbsp; {_clean_text(edu)}", style_education))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
