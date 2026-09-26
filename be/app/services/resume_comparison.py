import re


SECTION_HEADERS = [
    "NAME AND CONTACT",
    "PROFESSIONAL SUMMARY",
    "TECHNICAL SKILLS",
    "PROFESSIONAL EXPERIENCE",
    "EXPERIENCE",
    "PROJECTS",
    "EDUCATION",
    "CERTIFICATIONS",
    "CORE STRENGTHS",
    "KEYWORDS"
]


SKILL_GROUPS = {
    "Python": ["python"],
    "SQL": ["sql", "mysql", "postgresql", "sql server", "relational database", "relational databases"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Scikit-learn": ["scikit-learn", "sklearn"],
    "Machine Learning": ["machine learning", "ml model", "ml models", "classification", "regression", "model building"],
    "Deep Learning": ["deep learning"],
    "NLP": ["nlp", "natural language processing"],
    "LLMs": ["llm", "llms", "large language model", "large language models", "gpt"],
    "Prompt Engineering": ["prompt engineering", "prompt templates", "prompt design"],
    "RAG": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
    "OpenAI API": ["openai api", "openai gpt api", "gpt api"],
    "LangChain": ["langchain"],
    "LlamaIndex": ["llamaindex", "llama index"],
    "Hugging Face": ["hugging face", "huggingface", "hugging face transformers", "transformers"],
    "Embeddings": ["embedding", "embeddings"],
    "Semantic Search": ["semantic search", "similarity search", "similarity scoring"],
    "Vector Database": [
        "vector database",
        "vector databases",
        "vector db",
        "vector store",
        "vector stores",
        "faiss",
        "chromadb",
        "chroma db",
        "pinecone",
        "weaviate"
    ],
    "FAISS": ["faiss"],
    "ChromaDB": ["chromadb", "chroma db", "chroma"],
    "Pinecone": ["pinecone"],
    "Weaviate": ["weaviate"],
    "FastAPI": ["fastapi"],
    "Flask": ["flask"],
    "Streamlit": ["streamlit"],
    "Gradio": ["gradio"],
    "REST API": ["rest api", "rest apis", "api integration", "api integrations", "backend api", "backend apis"],
    "PyTorch": ["pytorch"],
    "TensorFlow": ["tensorflow"],
    "MLflow": ["mlflow"],
    "Docker": ["docker", "containerization", "containerized"],
    "Kubernetes": ["kubernetes", "k8s"],
    "Git": ["git", "github", "version control"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
    "AWS": ["aws", "amazon web services", "ec2", "s3", "aws bedrock"],
    "Azure": ["azure", "azure app service", "azure openai"],
    "GCP": ["gcp", "google cloud", "vertex ai"],
    "Airflow": ["airflow"],
    "Jupyter Notebook": ["jupyter notebook", "jupyter"],
    "VS Code": ["vs code", "vscode"],
    "Matplotlib": ["matplotlib"],
    "Seaborn": ["seaborn"],
    "Power BI": ["power bi"],
    "Tableau": ["tableau"],
    "Excel": ["excel"]
}


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def extract_section(resume_text: str, section_name: str) -> str:
    text = clean_text(resume_text)

    if not text:
        return ""

    headers_pattern = "|".join([re.escape(header) for header in SECTION_HEADERS])

    pattern = (
        rf"{re.escape(section_name)}\s*:?\s*"
        rf"(.*?)"
        rf"(?=\s*(?:{headers_pattern})\s*:?\s*|\Z)"
    )

    match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)

    if not match:
        return ""

    return clean_text(match.group(1))


def find_skill_label(text: str, aliases: list) -> str:
    if not text:
        return ""

    text_lower = text.lower()

    aliases_sorted = sorted(aliases, key=len, reverse=True)

    for alias in aliases_sorted:
        alias_lower = alias.lower().strip()

        if not alias_lower:
            continue

        pattern = rf"\b{re.escape(alias_lower)}\b"

        if re.search(pattern, text_lower, flags=re.IGNORECASE):
            return alias

    return ""


def get_skill_source_text(resume_text: str) -> str:
    technical_skills = extract_section(resume_text, "TECHNICAL SKILLS")
    keywords = extract_section(resume_text, "KEYWORDS")
    projects = extract_section(resume_text, "PROJECTS")
    experience = extract_section(resume_text, "PROFESSIONAL EXPERIENCE")

    combined_text = "\n".join(
        [
            technical_skills,
            keywords,
            projects,
            experience
        ]
    )

    if combined_text.strip():
        return combined_text

    return resume_text


def extract_present_skill_labels(resume_text: str) -> list:
    source_text = get_skill_source_text(resume_text)

    skills = []

    for canonical_skill, aliases in SKILL_GROUPS.items():
        matched_label = find_skill_label(source_text, aliases)

        if matched_label:
            skills.append(canonical_skill)

    return sorted(set(skills), key=str.lower)


def build_technical_skill_comparison(
    original_resume: str,
    optimized_resume: str
) -> list:
    original_source_text = get_skill_source_text(original_resume)
    optimized_source_text = get_skill_source_text(optimized_resume)

    rows = []

    for canonical_skill, aliases in SKILL_GROUPS.items():
        original_label = find_skill_label(original_source_text, aliases)
        optimized_label = find_skill_label(optimized_source_text, aliases)

        original_present = bool(original_label)
        optimized_present = bool(optimized_label)

        if not original_present and not optimized_present:
            continue

        if original_present and optimized_present:
            if original_label.lower() == optimized_label.lower():
                status = "Present in Both"
                comparison = f"{original_label} is present in both resumes."
            else:
                status = "Similar / Reworded"
                comparison = f"{original_label} in original is represented as {optimized_label} in optimized resume."

        elif original_present and not optimized_present:
            status = "Only in Original"
            comparison = f"{original_label} is present in original resume but not clearly shown in optimized resume."

        else:
            status = "Only in Optimized"
            comparison = f"{optimized_label} is shown in optimized resume but was not clearly found in original resume."

        rows.append(
            {
                "Skill": canonical_skill,
                "Original Skill": original_label if original_label else "-",
                "Optimized Skill": optimized_label if optimized_label else "-",
                "Original": 1 if original_present else 0,
                "Optimized": 1 if optimized_present else 0,
                "Status": status,
                "Comparison": comparison
            }
        )

    return rows


def build_resume_comparison(
    job_requirement_text: str,
    original_resume: str,
    optimized_resume: str,
    original_match_percentage: int,
    optimized_match_percentage: int
) -> dict:
    original_professional_summary = extract_section(
        original_resume,
        "PROFESSIONAL SUMMARY"
    )

    optimized_professional_summary = extract_section(
        optimized_resume,
        "PROFESSIONAL SUMMARY"
    )

    original_technical_skills_text = extract_section(
        original_resume,
        "TECHNICAL SKILLS"
    )

    optimized_technical_skills_text = extract_section(
        optimized_resume,
        "TECHNICAL SKILLS"
    )

    original_technical_skills = extract_present_skill_labels(original_resume)
    optimized_technical_skills = extract_present_skill_labels(optimized_resume)

    technical_skill_comparison = build_technical_skill_comparison(
        original_resume=original_resume,
        optimized_resume=optimized_resume
    )

    improvement = optimized_match_percentage - original_match_percentage

    return {
        "original_professional_summary": original_professional_summary,
        "optimized_professional_summary": optimized_professional_summary,
        "original_technical_skills": original_technical_skills,
        "optimized_technical_skills": optimized_technical_skills,
        "technical_skill_comparison": technical_skill_comparison,
        "comparison_data": {
            "overall_match": {
                "original_match_percentage": original_match_percentage,
                "optimized_match_percentage": optimized_match_percentage,
                "improvement_percentage": improvement
            },
            "professional_summary": {
                "original_text": original_professional_summary,
                "optimized_text": optimized_professional_summary
            },
            "technical_skills": {
                "original_text": original_technical_skills_text,
                "optimized_text": optimized_technical_skills_text,
                "original_skills": original_technical_skills,
                "optimized_skills": optimized_technical_skills,
                "skill_comparison": technical_skill_comparison
            }
        }
    }