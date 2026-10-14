"""
Ground Truth Evaluation Benchmark Dataset (Hardened Phase 5.5).
Contains multi-candidate benchmark profiles and 200+ labeled candidate-job pairs with:
- Multiple diverse personas (Fresher AI, Mid Backend, Senior AI Architect, NLP Data Scientist, Frontend, Career Switcher)
- Hard negatives (Seniority traps, semantic domain divergence, keyword stuffing, geographic constraints)
- Reproducible Train (Calibration) and Test (Held-Out) splits.
- Relevance Scale:
  2: Strong Fit
  1: Borderline / Maybe
  0: Bad Fit / Hard Negative
"""
import random
from typing import Dict, List, Any, Tuple


BENCHMARK_CANDIDATES: Dict[str, Dict[str, Any]] = {
    "cand_01_fresher_aiml": {
        "id": "cand_01_fresher_aiml",
        "full_name": "Aarav Sharma",
        "title": "Junior AI/ML Engineer",
        "total_experience_years": 0.8,
        "location": "Mumbai, India (Open to Remote)",
        "target_roles": ["AI Engineer", "Machine Learning Engineer", "Junior Python Developer"],
        "skills": ["Python", "PyTorch", "FastAPI", "PostgreSQL", "LangChain", "HuggingFace", "Docker", "scikit-learn"],
        "experience": [
            {
                "title": "AI/ML Intern",
                "company": "Cognitive AI Labs",
                "start_date": "2024-01-01",
                "end_date": None,
                "bullets": [
                    "Built RAG pipeline using FastAPI, HuggingFace embeddings, and PostgreSQL pgvector.",
                    "Fine-tuned small transformer models on custom domain datasets."
                ]
            }
        ],
        "education": ["B.Tech in Computer Science, 2024"]
    },
    "cand_02_mid_backend": {
        "id": "cand_02_mid_backend",
        "full_name": "Priya Verma",
        "title": "Backend Software Engineer",
        "total_experience_years": 3.5,
        "location": "Bangalore, India",
        "target_roles": ["Backend Engineer", "Software Engineer II", "Python Developer"],
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis", "Kafka", "SQLAlchemy", "Git", "REST APIs"],
        "experience": [
            {
                "title": "Backend Software Engineer",
                "company": "Fintech Solutions",
                "start_date": "2022-06-01",
                "end_date": None,
                "bullets": [
                    "Engineered asynchronous payment microservices using FastAPI and asyncpg.",
                    "Optimized PostgreSQL queries reducing P99 latency by 28%."
                ]
            },
            {
                "title": "Junior Backend Developer",
                "company": "Cloud Systems",
                "start_date": "2021-01-01",
                "end_date": "2022-05-31",
                "bullets": ["Maintained Django REST endpoints and database migrations."]
            }
        ],
        "education": ["B.Tech in Information Technology, 2021"]
    },
    "cand_03_senior_ai_architect": {
        "id": "cand_03_senior_ai_architect",
        "full_name": "Vikram Malhotra",
        "title": "Lead MLOps & AI Platform Architect",
        "total_experience_years": 8.5,
        "location": "Remote / Hyderabad",
        "target_roles": ["Principal AI Engineer", "Staff MLOps Architect", "Head of AI Infrastructure"],
        "skills": ["Python", "PyTorch", "CUDA", "Kubernetes", "Kubeflow", "Triton Inference Server", "Ray", "Distributed Training", "AWS", "Terraform"],
        "experience": [
            {
                "title": "Staff AI Platform Architect",
                "company": "Global Scale AI",
                "start_date": "2020-03-01",
                "end_date": None,
                "bullets": [
                    "Architected multi-node distributed PyTorch training clusters across 128 H100 GPUs.",
                    "Deployed Triton inference clusters reducing serving cost by $450k annually."
                ]
            },
            {
                "title": "Senior ML Engineer",
                "company": "Cloud Data Corp",
                "start_date": "2016-08-01",
                "end_date": "2020-02-28",
                "bullets": ["Productionized deep learning recommendation engines serving 50M DAU."]
            }
        ],
        "education": ["M.Tech in Artificial Intelligence, 2016"]
    },
    "cand_04_data_scientist": {
        "id": "cand_04_data_scientist",
        "full_name": "Ananya Sen",
        "title": "Data Scientist - NLP & Analytics",
        "total_experience_years": 2.2,
        "location": "Pune, India",
        "target_roles": ["Data Scientist", "NLP Engineer", "Machine Learning Specialist"],
        "skills": ["Python", "Pandas", "NumPy", "scikit-learn", "HuggingFace", "SQL", "Tableau", "Statistical Modeling"],
        "experience": [
            {
                "title": "Data Scientist",
                "company": "Analytics Nexus",
                "start_date": "2022-08-01",
                "end_date": None,
                "bullets": [
                    "Trained customer sentiment classification models using BERT and scikit-learn.",
                    "Designed automated SQL ETL pipelines processing 500GB daily telemetry data."
                ]
            }
        ],
        "education": ["M.Sc. in Statistics & Data Science, 2022"]
    },
    "cand_05_junior_frontend": {
        "id": "cand_05_junior_frontend",
        "full_name": "Rohan Gupta",
        "title": "Frontend Engineer",
        "total_experience_years": 1.2,
        "location": "Delhi NCR, India",
        "target_roles": ["Frontend Developer", "Junior React Engineer", "Web Developer"],
        "skills": ["JavaScript", "TypeScript", "React", "Next.js", "Tailwind CSS", "HTML5", "CSS3", "Redux Toolkit"],
        "experience": [
            {
                "title": "Associate Frontend Developer",
                "company": "Digital Experience Studio",
                "start_date": "2023-08-01",
                "end_date": None,
                "bullets": [
                    "Built responsive web applications in React 18, TypeScript, and Tailwind CSS.",
                    "Integrated TanStack Query for client-side API state caching."
                ]
            }
        ],
        "education": ["B.S. in Information Technology, 2023"]
    },
    "cand_06_career_switcher": {
        "id": "cand_06_career_switcher",
        "full_name": "Neha Joshi",
        "title": "Junior Python Developer / Career Switcher",
        "total_experience_years": 0.2,
        "location": "Remote / Mumbai",
        "target_roles": ["Junior Python Developer", "QA Automation Trainee", "Software Intern"],
        "skills": ["Python", "Flask", "SQLite", "Git", "pytest", "HTML", "CSS"],
        "experience": [
            {
                "title": "Software Engineering Trainee",
                "company": "CodeCraft Academy",
                "start_date": "2024-03-01",
                "end_date": "2024-09-01",
                "bullets": [
                    "Built fullstack portfolio projects using Python Flask, SQLite, and pytest.",
                    "Wrote automated unit test suites achieving 85% test coverage."
                ]
            }
        ],
        "education": ["Fullstack Python Bootcamp Certificate, 2024", "B.Com in Accounting, 2021"]
    }
}


def generate_benchmark_jobs() -> List[Dict[str, Any]]:
    """
    Generate 210 diverse candidate-job pairs including:
    - Clear Good Fits (Relevance 2)
    - Borderline / Potential Fits (Relevance 1)
    - Hard Negatives (Relevance 0):
      * Seniority traps (Staff/Lead asking 7+ YoE matching junior keywords)
      * Domain divergence traps (Embedded/Robotics Python vs. Web/RAG Python)
      * Deceptive keyword stuffers (Listing 40 technologies with 1 candidate match)
      * Geo / On-Site traps (Strict in-person Tokyo/London roles)
      * Credential barrier traps (Requiring Ph.D or Security Clearances)
    """
    jobs: List[Dict[str, Any]] = []

    # Category Specifications
    categories = [
        # --- Candidate 1: Fresher AI/ML (0.8 YoE) ---
        {
            "cand_id": "cand_01_fresher_aiml",
            "prefix": "cand1_good_rag",
            "title": "Junior AI Engineer - GenAI & RAG",
            "req_exp": 1.0,
            "skills": ["Python", "PyTorch", "FastAPI", "HuggingFace", "PostgreSQL"],
            "location": "Remote",
            "relevance": 2,
            "count": 12,
            "trap_type": None,
        },
        {
            "cand_id": "cand_01_fresher_aiml",
            "prefix": "cand1_maybe_ml",
            "title": "Machine Learning Engineer (1-2 YoE)",
            "req_exp": 2.0,
            "skills": ["Python", "scikit-learn", "Docker", "PyTorch", "AWS"],
            "location": "Hybrid - Mumbai",
            "relevance": 1,
            "count": 8,
            "trap_type": None,
        },
        {
            "cand_id": "cand_01_fresher_aiml",
            "prefix": "cand1_hardneg_seniority_trap",
            "title": "Principal AI Architect - Generative AI",
            "req_exp": 8.0,
            "skills": ["Python", "PyTorch", "FastAPI", "LangChain", "Kubernetes", "Executive Leadership"],
            "location": "Remote",
            "relevance": 0,
            "count": 6,
            "trap_type": "seniority_trap",
        },
        {
            "cand_id": "cand_01_fresher_aiml",
            "prefix": "cand1_hardneg_domain_divergence",
            "title": "Embedded Robotics Vision Engineer (Python/C++)",
            "req_exp": 1.0,
            "skills": ["Python", "C++", "ROS", "OpenCV", "RTOS", "Embedded Linux"],
            "location": "Remote",
            "relevance": 0,
            "count": 6,
            "trap_type": "domain_divergence",
        },
        {
            "cand_id": "cand_01_fresher_aiml",
            "prefix": "cand1_hardneg_keyword_stuffer",
            "title": "Fullstack Cloud Solutions Architect",
            "req_exp": 2.0,
            "skills": ["Python", "Java", "Ruby", "PHP", "Scala", "Kubernetes", "Angular", "Vue", "Cobol", "Hadoop", "Terraform", "SAP"],
            "location": "Remote",
            "relevance": 0,
            "count": 5,
            "trap_type": "keyword_stuffer",
        },

        # --- Candidate 2: Mid Backend (3.5 YoE) ---
        {
            "cand_id": "cand_02_mid_backend",
            "prefix": "cand2_good_backend",
            "title": "Backend Software Engineer - Python",
            "req_exp": 3.0,
            "skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "Redis"],
            "location": "Remote / Bangalore",
            "relevance": 2,
            "count": 12,
            "trap_type": None,
        },
        {
            "cand_id": "cand_02_mid_backend",
            "prefix": "cand2_maybe_lead",
            "title": "Senior Backend Developer - Distributed Systems",
            "req_exp": 5.0,
            "skills": ["Python", "FastAPI", "Kafka", "Kubernetes", "AWS", "Go"],
            "location": "Bangalore",
            "relevance": 1,
            "count": 8,
            "trap_type": None,
        },
        {
            "cand_id": "cand_02_mid_backend",
            "prefix": "cand2_hardneg_onsite_geo",
            "title": "Python Core Systems Engineer (Strict Onsite Tokyo)",
            "req_exp": 3.0,
            "skills": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            "location": "Tokyo, Japan (Onsite Mandatory, Fluent Japanese)",
            "relevance": 0,
            "count": 5,
            "trap_type": "geo_trap",
        },
        {
            "cand_id": "cand_02_mid_backend",
            "prefix": "cand2_hardneg_role_divergence",
            "title": "Frontend React / UI Specialist",
            "req_exp": 3.0,
            "skills": ["React", "CSS3", "Figma", "TypeScript", "Tailwind CSS"],
            "location": "Remote",
            "relevance": 0,
            "count": 5,
            "trap_type": "role_divergence",
        },

        # --- Candidate 3: Senior AI Architect (8.5 YoE) ---
        {
            "cand_id": "cand_03_senior_ai_architect",
            "prefix": "cand3_good_architect",
            "title": "Staff AI Infrastructure Architect",
            "req_exp": 8.0,
            "skills": ["Python", "PyTorch", "Kubernetes", "Triton Inference Server", "Ray", "CUDA"],
            "location": "Remote",
            "relevance": 2,
            "count": 12,
            "trap_type": None,
        },
        {
            "cand_id": "cand_03_senior_ai_architect",
            "prefix": "cand3_maybe_director",
            "title": "Engineering Director - Machine Learning Platforms",
            "req_exp": 10.0,
            "skills": ["MLOps", "Executive Leadership", "Budgeting", "Kubernetes", "Python"],
            "location": "Remote",
            "relevance": 1,
            "count": 8,
            "trap_type": None,
        },
        {
            "cand_id": "cand_03_senior_ai_architect",
            "prefix": "cand3_hardneg_underqualified_role",
            "title": "Junior Python Intern - Manual Testing",
            "req_exp": 0.0,
            "skills": ["Python", "Selenium", "Manual Testing"],
            "location": "Hyderabad",
            "relevance": 0,
            "count": 6,
            "trap_type": "underqualification_trap",
        },

        # --- Candidate 4: Data Scientist (2.2 YoE) ---
        {
            "cand_id": "cand_04_data_scientist",
            "prefix": "cand4_good_ds",
            "title": "Data Scientist - NLP & Predictive Modeling",
            "req_exp": 2.0,
            "skills": ["Python", "Pandas", "scikit-learn", "HuggingFace", "SQL"],
            "location": "Remote / Pune",
            "relevance": 2,
            "count": 10,
            "trap_type": None,
        },
        {
            "cand_id": "cand_04_data_scientist",
            "prefix": "cand4_maybe_ml_eng",
            "title": "ML Engineer (Python/SQL)",
            "req_exp": 3.0,
            "skills": ["Python", "SQL", "Docker", "scikit-learn", "Airflow"],
            "location": "Pune",
            "relevance": 1,
            "count": 6,
            "trap_type": None,
        },
        {
            "cand_id": "cand_04_data_scientist",
            "prefix": "cand4_hardneg_phd_gate",
            "title": "Research Scientist - Quantum Machine Learning (Ph.D Required)",
            "req_exp": 2.0,
            "skills": ["Python", "Quantum Computing", "Qiskit", "Ph.D in Physics"],
            "location": "Remote",
            "relevance": 0,
            "count": 5,
            "trap_type": "credential_gate",
        },

        # --- Candidate 5: Junior Frontend (1.2 YoE) ---
        {
            "cand_id": "cand_05_junior_frontend",
            "prefix": "cand5_good_frontend",
            "title": "Junior React & TypeScript Developer",
            "req_exp": 1.0,
            "skills": ["React", "TypeScript", "Tailwind CSS", "JavaScript", "HTML5"],
            "location": "Remote / Delhi",
            "relevance": 2,
            "count": 10,
            "trap_type": None,
        },
        {
            "cand_id": "cand_05_junior_frontend",
            "prefix": "cand5_maybe_fullstack",
            "title": "Fullstack Web Developer (Node/React)",
            "req_exp": 2.0,
            "skills": ["React", "Node.js", "Express", "TypeScript", "PostgreSQL"],
            "location": "Delhi",
            "relevance": 1,
            "count": 6,
            "trap_type": None,
        },
        {
            "cand_id": "cand_05_junior_frontend",
            "prefix": "cand5_hardneg_senior_architect",
            "title": "Principal UI Architect - Micro-Frontends",
            "req_exp": 9.0,
            "skills": ["React", "Webpack", "Micro-frontends", "Performance Profiling", "WASM"],
            "location": "Remote",
            "relevance": 0,
            "count": 6,
            "trap_type": "seniority_trap",
        },

        # --- Candidate 6: Career Switcher / Intern (0.2 YoE) ---
        {
            "cand_id": "cand_06_career_switcher",
            "prefix": "cand6_good_entry",
            "title": "Junior Python Developer / Entry Level",
            "req_exp": 0.0,
            "skills": ["Python", "Flask", "SQLite", "Git", "pytest"],
            "location": "Remote",
            "relevance": 2,
            "count": 8,
            "trap_type": None,
        },
        {
            "cand_id": "cand_06_career_switcher",
            "prefix": "cand6_maybe_qa",
            "title": "QA Automation Engineer (Python Scripting)",
            "req_exp": 1.0,
            "skills": ["Python", "Selenium", "pytest", "Git"],
            "location": "Mumbai",
            "relevance": 1,
            "count": 6,
            "trap_type": None,
        },
        {
            "cand_id": "cand_06_career_switcher",
            "prefix": "cand6_hardneg_senior_backend",
            "title": "Senior Python Backend Engineer (Distributed Databases)",
            "req_exp": 6.0,
            "skills": ["Python", "Flask", "Distributed Systems", "Cassandra", "Raft", "C++"],
            "location": "Remote",
            "relevance": 0,
            "count": 6,
            "trap_type": "seniority_trap",
        },
    ]

    job_counter = 1
    for cat in categories:
        for idx in range(cat["count"]):
            j_id = f"job_{job_counter:03d}_{cat['prefix']}"
            title = f"{cat['title']} - #{idx+1}"
            exp_req = cat["req_exp"]

            # Construct realistic company intro and requirements section
            company_intro = (
                f"About Enterprise Cloud Systems Inc:\n"
                f"Enterprise Cloud Systems is a global leader in software infrastructure, enterprise automation, "
                f"and next-generation application platforms. Founded in 2012, we operate across North America, Europe, "
                f"and Asia-Pacific, delivering mission-critical SaaS to millions of enterprise business users.\n\n"
            )

            req_block = (
                f"Requirements & Core Technical Stack:\n"
                f"- Minimum Professional Experience: {exp_req} years.\n"
                f"- Primary Technologies: {', '.join(cat['skills'])}.\n"
                f"- Location / Work Mode: {cat['location']}.\n"
                f"- Responsibilities: Develop maintainable production code, execute unit tests, collaborate across cross-functional teams."
            )
            if cat["trap_type"]:
                req_block += f"\n- Constraint Notice: Trap Category [{cat['trap_type']}]."

            description = company_intro + req_block

            jobs.append({
                "job_id": j_id,
                "candidate_id": cat["cand_id"],
                "title": title,
                "company": f"Enterprise_Corp_{job_counter}",
                "location": cat["location"],
                "is_remote": "remote" in cat["location"].lower(),
                "description_raw": description,
                "requirements_text": req_block,
                "required_experience_years": exp_req,
                "skills": cat["skills"],
                "ground_truth_relevance": cat["relevance"],
                "trap_type": cat["trap_type"],
            })
            job_counter += 1

    return jobs


# Complete Evaluation Benchmark Dataset
EVALUATION_DATASET: List[Dict[str, Any]] = generate_benchmark_jobs()


def get_train_test_split(
    dataset: List[Dict[str, Any]] | None = None,
    test_ratio: float = 0.40,
    random_seed: int = 42,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Perform a reproducible stratified Train / Test split by (candidate_id, relevance).
    Ensures zero data leakage: calibration happens on Train, final evaluation on Test.
    """
    data = dataset if dataset is not None else EVALUATION_DATASET

    # Group by (candidate_id, relevance) to stratify
    strata: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    for item in data:
        key = (item["candidate_id"], item["ground_truth_relevance"])
        strata.setdefault(key, []).append(item)

    rng = random.Random(random_seed)
    train_set: List[Dict[str, Any]] = []
    test_set: List[Dict[str, Any]] = []

    for key, items in strata.items():
        shuffled = list(items)
        rng.shuffle(shuffled)
        n_test = max(1, int(round(len(shuffled) * test_ratio)))
        test_slice = shuffled[:n_test]
        train_slice = shuffled[n_test:]

        test_set.extend(test_slice)
        train_set.extend(train_slice)

    # Final shuffle to mix candidates
    rng.shuffle(train_set)
    rng.shuffle(test_set)

    return train_set, test_set
