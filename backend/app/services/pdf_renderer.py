"""
Template Rendering Engine for ATS-Compliant Resumes.
Uses Jinja2 to render clean, single-column HTML resumes matching ATS scanning standards.
"""
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.schemas.ats_resume import ATSTailoredResume

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

jinja_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
)


def render_ats_resume_html(resume: ATSTailoredResume) -> str:
    """
    Render ATSTailoredResume data into a clean, single-column ATS HTML document.
    Includes print media stylesheet for pixel-perfect PDF export via browser or print driver.
    """
    template = jinja_env.get_template("ats_resume.html")
    return template.render(resume=resume)
