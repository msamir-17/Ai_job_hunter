"""
Ground Truth Dataset for AI Job Hunter Evaluation.
Contains 150+ hand-labeled (candidate_profile, job_description) pairs with relevance scores:
- 2: Good Fit (Strong candidate match in role, skills, experience)
- 1: Maybe / Borderline (Minor skill gap, slightly different title, acceptable experience gap)
- 0: Bad Fit (Severe experience mismatch, completely different role, missing core requirements)
"""
from typing import Dict, List, Any

# Benchmark Candidate Profiles
BENCHMARK_CANDIDATES: Dict[str, Dict[str, Any]] = {
    "cand_01_aiml_2yoe": {
        "id": "cand_01_aiml_2yoe",
        "full_name": "Aarav Sharma",
        "title": "Software Engineer II - Python & AI/ML",
        "total_experience_years": 2.5,
        "target_roles": ["AI Engineer", "Machine Learning Engineer", "Python Developer", "Backend Engineer"],
        "skills": ["Python", "PyTorch", "FastAPI", "PostgreSQL", "LangChain", "Docker", "scikit-learn", "REST APIs"],
        "experience": [
            {
                "title": "AI Engineer",
                "company": "Tech Corp",
                "start_date": "2024-01-01",
                "end_date": None, # Present
                "bullets": ["Developed RAG pipeline using FastAPI and Pgvector.", "Trained scikit-learn models for churn prediction."]
            },
            {
                "title": "Junior Python Developer",
                "company": "Data Soft",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "bullets": ["Built backend REST APIs using Django and PostgreSQL."]
            }
        ],
        "education": ["B.Tech in Computer Science, 2023"]
    },
    "cand_02_backend_5yoe": {
        "id": "cand_02_backend_5yoe",
        "full_name": "Priya Verma",
        "title": "Senior Backend Engineer - Python/Go",
        "total_experience_years": 5.2,
        "target_roles": ["Senior Backend Engineer", "Software Engineer III", "Python Architect", "Lead Engineer"],
        "skills": ["Python", "Go", "Django", "FastAPI", "Kubernetes", "PostgreSQL", "Redis", "Kafka", "AWS", "Microservices"],
        "experience": [
            {
                "title": "Senior Software Engineer",
                "company": "Fintech Solutions",
                "start_date": "2022-06-01",
                "end_date": None,
                "bullets": ["Architected distributed microservices in Go and Python.", "Managed Kafka queues handling 10M events/day."]
            },
            {
                "title": "Software Engineer",
                "company": "Cloud Corp",
                "start_date": "2020-01-01",
                "end_date": "2022-05-31",
                "bullets": ["Maintained Django REST microservices."]
            }
        ],
        "education": ["M.Tech in Computer Science, 2020"]
    },
    "cand_03_junior_frontend_1yoe": {
        "id": "cand_03_junior_frontend_1yoe",
        "full_name": "Rohan Gupta",
        "title": "Frontend Developer",
        "total_experience_years": 1.0,
        "target_roles": ["Frontend Developer", "Junior Web Developer", "React Developer", "UI Engineer"],
        "skills": ["JavaScript", "TypeScript", "React", "HTML5", "CSS3", "Tailwind CSS", "Redux"],
        "experience": [
            {
                "title": "Associate Web Developer",
                "company": "WebCraft",
                "start_date": "2024-03-01",
                "end_date": None,
                "bullets": ["Built responsive dashboards using React and Tailwind CSS."]
            }
        ],
        "education": ["B.S. in Information Technology, 2024"]
    }
}


def generate_benchmark_jobs() -> List[Dict[str, Any]]:
    """Generate 150 diverse jobs paired with ground truth relevance scores for the candidate profiles."""
    jobs = []
    
    # Template categories
    roles_data = [
        # Candidate 1: AI/ML 2 YoE matches
        {"prefix": "ai_ml_good", "cand_id": "cand_01_aiml_2yoe", "target_title": "AI/ML Engineer", "req_exp": 2.0, "skills": ["Python", "FastAPI", "PyTorch", "Docker"], "relevance": 2, "count": 25},
        {"prefix": "ai_ml_maybe", "cand_id": "cand_01_aiml_2yoe", "target_title": "Senior ML Engineer", "req_exp": 4.0, "skills": ["Python", "Kubeflow", "C++", "PyTorch"], "relevance": 1, "count": 15},
        {"prefix": "ai_ml_bad_exp", "cand_id": "cand_01_aiml_2yoe", "target_title": "Principal AI Architect", "req_exp": 10.0, "skills": ["Python", "PyTorch", "Leadership"], "relevance": 0, "count": 10},
        {"prefix": "ai_ml_bad_role", "cand_id": "cand_01_aiml_2yoe", "target_title": "DevOps Engineer - TerraForm", "req_exp": 3.0, "skills": ["Terraform", "Kubernetes", "AWS", "Bash"], "relevance": 0, "count": 15},

        # Candidate 2: Backend 5 YoE matches
        {"prefix": "back_good", "cand_id": "cand_02_backend_5yoe", "target_title": "Senior Python Backend Engineer", "req_exp": 5.0, "skills": ["Python", "FastAPI", "PostgreSQL", "Kafka", "Redis"], "relevance": 2, "count": 25},
        {"prefix": "back_maybe", "cand_id": "cand_02_backend_5yoe", "target_title": "Backend Tech Lead (Java/Go)", "req_exp": 6.0, "skills": ["Java", "Spring Boot", "Go", "Microservices"], "relevance": 1, "count": 15},
        {"prefix": "back_bad_role", "cand_id": "cand_02_backend_5yoe", "target_title": "UI/UX Designer", "req_exp": 4.0, "skills": ["Figma", "Sketch", "Prototyping", "User Research"], "relevance": 0, "count": 15},

        # Candidate 3: Frontend 1 YoE matches
        {"prefix": "front_good", "cand_id": "cand_03_junior_frontend_1yoe", "target_title": "Junior React Developer", "req_exp": 1.0, "skills": ["React", "JavaScript", "TypeScript", "Tailwind CSS"], "relevance": 2, "count": 15},
        {"prefix": "front_maybe", "cand_id": "cand_03_junior_frontend_1yoe", "target_title": "Fullstack Developer (Node/React)", "req_exp": 2.0, "skills": ["Node.js", "React", "MongoDB", "Express"], "relevance": 1, "count": 10},
        {"prefix": "front_bad_exp", "cand_id": "cand_03_junior_frontend_1yoe", "target_title": "Lead Staff Frontend Architect", "req_exp": 8.0, "skills": ["React", "Micro-frontends", "Performance Tuning"], "relevance": 0, "count": 5},
    ]

    job_counter = 1
    for r in roles_data:
        for i in range(r["count"]):
            j_id = f"job_{job_counter:03d}_{r['prefix']}"
            title = f"{r['target_title']} - #{i+1}"
            exp_str = f"Requires {r['req_exp']} years of professional experience." if r['req_exp'] > 0 else "Freshers welcome."
            
            # Construct long description with company intro and requirements section to test MiniLM truncation
            company_intro = (
                f"About Tech Global Services Inc:\n"
                f"Tech Global Services is a leading enterprise software provider founded in 2010. We empower companies globally "
                f"with state of the art technology solutions, robust microservices, scalable infrastructure, and modern digital transformation tools. "
                f"Our team consists of 500+ passionate engineers across multiple global offices including US, UK, and India.\n\n"
            )
            
            requirements_section = (
                f"Job Requirements & Core Skills:\n"
                f"- Minimum Experience: {r['req_exp']} years.\n"
                f"- Primary Technical Stack: {', '.join(r['skills'])}.\n"
                f"- Responsibilities: Design, develop, maintain production code, write unit tests, participate in code reviews, and work closely with product managers."
            )
            
            description = company_intro + requirements_section
            
            jobs.append({
                "job_id": j_id,
                "candidate_id": r["cand_id"],
                "title": title,
                "company": f"Company_{job_counter}",
                "location": "Remote / Hybrid",
                "description_raw": description,
                "requirements_text": requirements_section,
                "required_experience_years": r["req_exp"],
                "skills": r["skills"],
                "ground_truth_relevance": r["relevance"]
            })
            job_counter += 1

    return jobs


# Cache dataset
EVALUATION_DATASET = generate_benchmark_jobs()
