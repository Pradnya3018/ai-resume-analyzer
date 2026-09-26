import json
import numpy as np
from openai import OpenAI
from typing import Optional

from app.core.config import settings


client = OpenAI(api_key=settings.OPENAI_API_KEY)


def get_embedding(text: str) -> np.ndarray:
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=text
    )

    return np.array(response.data[0].embedding, dtype=float)


def get_llm_resume_score(
    job_requirement_text: str,
    resume_text: str,
    embedding_similarity_percentage: int
) -> dict:
    prompt = f"""
You are an expert technical recruiter and resume screening assistant.

Your task:
Compare the job requirement with the uploaded resume and calculate a realistic match score.

Return only valid JSON with this exact structure:
{{
  "llm_match_percentage": 0,
  "matched_skills": [],
  "partially_matched_skills": [],
  "missing_skills": [],
  "summary": "",
  "recommendation": ""
}}

Scoring rules:
- Score must be from 0 to 100.
- Give high score when required skills are clearly present in the resume.
- Give credit when the resume describes practical use of a required skill, even if the wording is slightly different.
- Give partial credit when related skills or similar responsibilities are clearly present.
- Penalize missing mandatory skills.
- Do not give credit for skills that are not present or not supported.
- Do not over-score based only on generic experience.
- Give extra credit when skills are described in project or experience context.
- Embedding similarity percentage is only a supporting signal, not the final score.

How to identify skill evidence:
- A skill can be considered matched if it is directly listed in Skills, Experience, Projects, Certifications, or Keywords.
- A skill can be considered partially matched if related practical evidence exists.
- A skill must be considered missing if there is no clear evidence in the resume.

Embedding similarity percentage:
{embedding_similarity_percentage}

Job requirement text:
{job_requirement_text}

Resume text:
{resume_text}
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a strict but fair resume analyzer. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    return json.loads(content)


def extract_resume_supported_skills(resume_text: str) -> dict:
    prompt = f"""
You are a strict resume evidence extractor.

Your task:
Extract only the technical skills, tools, technologies, libraries, databases, platforms,
frameworks, methods, and role titles that are clearly supported by the original resume.

Return only valid JSON with this exact structure:
{{
  "supported_skills": [],
  "supported_role_titles": [],
  "skill_evidence": [],
  "evidence_summary": ""
}}

Extraction rules:
- Do NOT add skills from a job description.
- Do NOT invent skills.
- Do NOT infer unrelated skills.
- Extract exact skills that are written in the resume.
- Also extract clearly supported practical capabilities.
- If the resume says a project used OpenAI API, then OpenAI API is supported.
- If the resume says document chunks, embeddings, FAISS, ChromaDB, or semantic search, then those exact terms are supported.
- If the resume says FastAPI APIs, then FastAPI and REST API development are supported.
- If the resume says Streamlit UI, then Streamlit is supported.
- If the resume says Scikit-learn model, then Scikit-learn and machine learning model building are supported.
- If the resume says model evaluation metrics, then model evaluation is supported.
- Do not assume advanced skills unless the resume clearly supports them.

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You extract only resume-supported skills and evidence. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    return json.loads(content)


def optimize_resume_with_jd(
    job_requirement_text: str,
    resume_text: str,
    original_analysis: Optional[dict] = None,
    supported_resume_data: Optional[dict] = None,
    retry_mode: bool = False,
    blocked_keywords: Optional[list] = None
) -> dict:
    original_score = None
    matched_skills = []
    partially_matched_skills = []
    missing_skills = []

    if original_analysis:
        original_score = original_analysis.get("final_match_percentage")
        matched_skills = original_analysis.get("matched_skills", [])
        partially_matched_skills = original_analysis.get("partially_matched_skills", [])
        missing_skills = original_analysis.get("missing_skills", [])

    supported_skills = []
    supported_role_titles = []
    skill_evidence = []
    evidence_summary = ""

    if supported_resume_data:
        supported_skills = supported_resume_data.get("supported_skills", [])
        supported_role_titles = supported_resume_data.get("supported_role_titles", [])
        skill_evidence = supported_resume_data.get("skill_evidence", [])
        evidence_summary = supported_resume_data.get("evidence_summary", "")

    if blocked_keywords is None:
        blocked_keywords = []

    retry_instruction = ""

    if retry_mode:
        retry_instruction = """
Previous optimization either reduced the match score or added unsupported content.

Retry carefully:
- Keep all original resume-supported skills.
- Add stronger descriptions only for skills that already exist in the original resume.
- Do not add unsupported JD-only skills.
- Improve the Professional Summary, Technical Skills, and Keywords sections.
- Keep Experience and Projects factually same, but improve wording where useful.
- The optimized resume must maintain or improve the original match score.
"""

    prompt = f"""
You are an honest resume optimization assistant.

Your task:
Optimize the uploaded resume for the job description so that the match percentage improves,
but without hallucinating or adding unsupported technical skills.

Main goal:
Increase the match percentage by improving how existing resume-supported skills are described.
Do not add skills that are not supported by the original resume.

Current original match percentage:
{original_score}

Resume-supported skills:
{supported_skills}

Supported role titles:
{supported_role_titles}

Skill evidence from resume:
{skill_evidence}

Resume evidence summary:
{evidence_summary}

Original matched skills:
{matched_skills}

Original partially matched skills:
{partially_matched_skills}

JD skills missing from original resume:
{missing_skills}

Blocked keywords that must NOT be added:
{blocked_keywords}

Important truthfulness rules:
- Do NOT invent fake technical skills.
- Do NOT invent fake projects.
- Do NOT invent fake companies.
- Do NOT invent fake certifications.
- Do NOT invent fake job titles.
- Do NOT add a JD skill unless the original resume already supports it.
- Do NOT change the candidate's profile identity artificially.
- Do NOT exaggerate the candidate's experience.

Allowed optimization:
- Improve the Professional Summary by adding concise descriptions of resume-supported skills.
- Improve Technical Skills by grouping existing supported skills in JD-friendly categories.
- Improve Keywords by prioritizing supported terms that overlap with the JD.
- Improve bullet wording to make existing work sound clearer and more relevant.
- Keep the actual meaning of experience and projects unchanged.
- Keep Education and Certifications unchanged.

Profile Summary instructions:
- Add 2 to 4 concise lines that describe how the candidate used existing skills.
- Use only skills already supported in the original resume.
- Convert plain skill names into JD-aligned descriptions.
- Example style:
  "Experienced in building Python-based APIs and data processing workflows."
  "Hands-on exposure to embeddings, semantic search, and document retrieval where supported by project work."
  "Used FastAPI, Streamlit, SQL, and Git for building and maintaining internal applications."
- Do not use the example skills unless they are supported by the original resume.
- Do not keyword-stuff.
- Make the summary stronger but realistic.

Technical Skills instructions:
- Reorganize existing supported skills into clear categories.
- Use categories only when the resume supports them.
- Possible categories:
  Programming, Backend/API Development, AI/ML, LLM & GenAI, Vector Search, Data Processing,
  Databases, Cloud/DevOps, Tools, Reporting.
- Do not create a category if there are no supported skills for that category.
- Add short descriptive labels where helpful.
- Example:
  "Vector Search & Retrieval: FAISS, ChromaDB, embeddings, semantic search"
  only if those terms exist in the original resume.

Experience and Project instructions:
- Preserve all real companies, dates, project names, and responsibilities.
- You may improve wording to highlight supported JD-aligned skills.
- Do not add new tools to a project unless those tools are already present in the original resume.
- Do not add new responsibilities that are not supported.
- Add technical context around supported skills when it improves clarity.

Keyword instructions:
- Add only supported keywords.
- Prioritize skills that overlap between the JD and resume.
- If a JD skill is not supported by the original resume, do not add it.
- Put unsupported JD skills in not_added_keywords.

Output quality target:
- The optimized resume should be stronger, more descriptive, and more JD-aligned.
- It should normally improve the match percentage when the original resume already contains relevant skills.
- If improvement is not possible without adding unsupported skills, keep the resume truthful.

{retry_instruction}

Formatting rules for optimized_resume:
- The optimized_resume must be returned as properly formatted resume text.
- Do NOT return the optimized resume as one paragraph.
- Use clear section headers in uppercase.
- Use newline characters between sections.
- Use bullet points under experience and projects.
- Do not include "Page 1", "Page 2", or PDF extraction artifacts.
- Keep the resume readable and ATS-friendly.

Required resume section format:
NAME AND CONTACT
PROFESSIONAL SUMMARY
TECHNICAL SKILLS
PROFESSIONAL EXPERIENCE
PROJECTS
EDUCATION
CERTIFICATIONS
CORE STRENGTHS
KEYWORDS

Professional Summary rules:
- Add only 2 to 4 concise lines.
- Improve the summary using only resume-supported skills.
- Describe existing skills in a JD-aligned way.
- Do not add unsupported technical skills.
- Do not change the candidate profile artificially.

Example of allowed enhancement:
If original resume has "FastAPI", you may write:
"Experienced in building Python-based backend APIs using FastAPI."

If original resume has "OpenAI API", you may write:
"Hands-on experience integrating OpenAI API for AI-enabled application workflows."

If original resume has "embeddings" and "FAISS", you may write:
"Worked with embeddings and FAISS-based semantic search for document retrieval."

Do not use any example skill unless it exists in the original resume.



Return only valid JSON with this exact structure:
{{
  "optimized_resume": "",
  "added_or_improved_keywords": [],
  "not_added_keywords": [],
  "changes_summary": "",
  "warning": ""
}}

Job description:
{job_requirement_text}

Original resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You optimize resumes honestly by expanding only resume-supported skills into stronger JD-aligned descriptions. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.15,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    return json.loads(content)


def validate_optimized_resume_against_original(
    original_resume: str,
    optimized_resume: str
) -> dict:
    prompt = f"""
You are a strict but fair resume validation checker.

Compare the original resume and optimized resume.

Your task:
Check whether the optimized resume added unsupported skills, tools, technologies,
job titles, certifications, projects, responsibilities, or claims.

Return only valid JSON with this exact structure:
{{
  "is_valid": true,
  "unsupported_claims": [],
  "validation_summary": ""
}}

Validation rules:
- Formatting improvements are valid.
- Grammar improvements are valid.
- Reorganizing skills is valid.
- Rewording existing responsibilities is valid.
- Adding stronger descriptions of existing resume-supported skills is valid.
- Adding JD-aligned wording is valid only when the underlying skill exists in the original resume.
- Adding a new unsupported technical skill is invalid.
- Adding a new unsupported project is invalid.
- Adding a new unsupported certification is invalid.
- Adding a new unsupported job title is invalid.
- Changing the candidate's profile identity is invalid unless the original resume supports it.

Important:
If the original resume contains a skill and the optimized resume describes that skill better,
that is valid.

Examples of valid changes:
- Original has "FastAPI"; optimized says "FastAPI backend API development".
- Original has "OpenAI API"; optimized says "OpenAI GPT API integration".
- Original has "FAISS"; optimized says "FAISS-based vector search".
- Original has "Scikit-learn"; optimized says "Scikit-learn ML workflows".
- Original has "model evaluation"; optimized says "model evaluation using accuracy, precision, recall, and F1-score".

Examples of invalid changes:
- Original does not mention FastAPI, but optimized adds FastAPI.
- Original does not mention OpenAI, but optimized adds OpenAI API.
- Original does not mention RAG, embeddings, vector DB, or semantic search, but optimized adds them.
- Original is Data Analyst only, but optimized changes the title to AI Engineer without supporting AI project evidence.

Original resume:
{original_resume}

Optimized resume:
{optimized_resume}
"""

    response = client.chat.completions.create(
        model=settings.OPENAI_CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You validate resume truthfulness. Improved descriptions of existing skills are valid; unsupported new claims are invalid. Return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    content = response.choices[0].message.content
    return json.loads(content)