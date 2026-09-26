import numpy as np

from app.core.config import settings
from app.services.openai_service import get_embedding, get_llm_resume_score


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    denominator = np.linalg.norm(vec1) * np.linalg.norm(vec2)

    if denominator == 0:
        return 0.0

    return float(np.dot(vec1, vec2) / denominator)


def analyze_resume_match(job_requirement_text: str, resume_text: str) -> dict:
    job_requirement_text = job_requirement_text[:settings.MAX_JOB_CHARS]
    resume_text = resume_text[:settings.MAX_RESUME_CHARS]

    job_embedding = get_embedding(job_requirement_text)
    resume_embedding = get_embedding(resume_text)

    similarity = cosine_similarity(job_embedding, resume_embedding)
    embedding_similarity_percentage = round(similarity * 100)

    llm_result = get_llm_resume_score(
        job_requirement_text=job_requirement_text,
        resume_text=resume_text,
        embedding_similarity_percentage=embedding_similarity_percentage
    )

    llm_match_percentage = int(llm_result.get("llm_match_percentage", 0))

    final_match_percentage = round(
        (0.7 * llm_match_percentage) + (0.3 * embedding_similarity_percentage)
    )

    final_match_percentage = max(0, min(100, final_match_percentage))

    return {
        "final_match_percentage": final_match_percentage,
        "llm_match_percentage": llm_match_percentage,
        "embedding_similarity_percentage": embedding_similarity_percentage,
        "matched_skills": llm_result.get("matched_skills", []),
        "partially_matched_skills": llm_result.get("partially_matched_skills", []),
        "missing_skills": llm_result.get("missing_skills", []),
        "summary": llm_result.get("summary", ""),
        "recommendation": llm_result.get("recommendation", "")
    }