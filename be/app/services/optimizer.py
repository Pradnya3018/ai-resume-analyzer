import logging

from app.core.config import settings
from app.services.analyzer import analyze_resume_match
from app.services.openai_service import (
    extract_resume_supported_skills,
    optimize_resume_with_jd,
    validate_optimized_resume_against_original
)
from app.services.resume_comparison import build_resume_comparison


logger = logging.getLogger("resume_analyzer_backend")


def create_comparison_result(
    job_requirement_text: str,
    original_resume: str,
    optimized_resume: str,
    original_score: int,
    optimized_score: int
) -> dict:
    try:
        return build_resume_comparison(
            job_requirement_text=job_requirement_text,
            original_resume=original_resume,
            optimized_resume=optimized_resume,
            original_match_percentage=original_score,
            optimized_match_percentage=optimized_score
        )

    except Exception as error:
        logger.exception("Failed to build resume comparison data.")

        return {
            "original_professional_summary": "",
            "optimized_professional_summary": "",
            "original_technical_skills": [],
            "optimized_technical_skills": [],
            "technical_skill_comparison": [],
            "comparison_data": {
                "error": str(error),
                "overall_match": {
                    "original_match_percentage": original_score,
                    "optimized_match_percentage": optimized_score,
                    "improvement_percentage": optimized_score - original_score
                },
                "professional_summary": {
                    "original_text": "",
                    "optimized_text": ""
                },
                "technical_skills": {
                    "original_text": "",
                    "optimized_text": "",
                    "original_skills": [],
                    "optimized_skills": [],
                    "skill_comparison": []
                }
            }
        }


def optimize_resume(job_requirement_text: str, resume_text: str) -> dict:
    job_requirement_text = job_requirement_text[:settings.MAX_JOB_CHARS]
    resume_text = resume_text[:settings.MAX_RESUME_CHARS]

    logger.info("Starting original resume analysis before optimization.")

    original_analysis = analyze_resume_match(
        job_requirement_text=job_requirement_text,
        resume_text=resume_text
    )

    original_score = original_analysis["final_match_percentage"]

    logger.info(f"Original resume match score: {original_score}")

    logger.info("Extracting skills strictly supported by original resume.")

    supported_resume_data = extract_resume_supported_skills(
        resume_text=resume_text
    )

    logger.info(
        f"Supported skills extracted: {supported_resume_data.get('supported_skills', [])}"
    )

    logger.info("Starting first strict resume optimization attempt.")

    first_optimization = optimize_resume_with_jd(
        job_requirement_text=job_requirement_text,
        resume_text=resume_text,
        original_analysis=original_analysis,
        supported_resume_data=supported_resume_data,
        retry_mode=False
    )

    first_optimized_resume = first_optimization.get("optimized_resume", "")

    first_validation = validate_optimized_resume_against_original(
        original_resume=resume_text,
        optimized_resume=first_optimized_resume
    )

    first_is_valid = first_validation.get("is_valid", False)
    first_unsupported_claims = first_validation.get("unsupported_claims", [])

    logger.info(f"First optimization valid: {first_is_valid}")
    logger.info(f"First unsupported claims: {first_unsupported_claims}")

    best_result = first_optimization
    best_resume = first_optimized_resume
    best_score = original_score
    best_is_valid = first_is_valid

    if first_is_valid:
        first_analysis = analyze_resume_match(
            job_requirement_text=job_requirement_text,
            resume_text=first_optimized_resume
        )

        first_score = first_analysis["final_match_percentage"]

        logger.info(f"First optimized resume match score: {first_score}")

        best_score = first_score

    if (not first_is_valid) or (best_score < original_score):
        logger.warning(
            "First optimization failed validation or reduced score. Starting strict retry."
        )

        retry_optimization = optimize_resume_with_jd(
            job_requirement_text=job_requirement_text,
            resume_text=resume_text,
            original_analysis=original_analysis,
            supported_resume_data=supported_resume_data,
            retry_mode=True,
            blocked_keywords=first_unsupported_claims
        )

        retry_optimized_resume = retry_optimization.get("optimized_resume", "")

        retry_validation = validate_optimized_resume_against_original(
            original_resume=resume_text,
            optimized_resume=retry_optimized_resume
        )

        retry_is_valid = retry_validation.get("is_valid", False)
        retry_unsupported_claims = retry_validation.get("unsupported_claims", [])

        logger.info(f"Retry optimization valid: {retry_is_valid}")
        logger.info(f"Retry unsupported claims: {retry_unsupported_claims}")

        if retry_is_valid:
            retry_analysis = analyze_resume_match(
                job_requirement_text=job_requirement_text,
                resume_text=retry_optimized_resume
            )

            retry_score = retry_analysis["final_match_percentage"]

            logger.info(f"Retry optimized resume match score: {retry_score}")

            if retry_score >= best_score:
                best_result = retry_optimization
                best_resume = retry_optimized_resume
                best_score = retry_score
                best_is_valid = True

    if (not best_is_valid) or (best_score < original_score):
        logger.warning(
            "Optimization could not safely improve or maintain score. "
            "Returning original resume."
        )

        comparison_result = create_comparison_result(
            job_requirement_text=job_requirement_text,
            original_resume=resume_text,
            optimized_resume=resume_text,
            original_score=original_score,
            optimized_score=original_score
        )

        return {
            "original_match_percentage": original_score,
            "optimized_match_percentage": original_score,
            "improvement_percentage": 0,
            "optimized_resume": resume_text,
            "added_or_improved_keywords": [],
            "not_added_keywords": original_analysis.get("missing_skills", []),
            "changes_summary": (
                "Optimization was not applied because the generated version either "
                "added unsupported skills or reduced the match percentage. "
                "The original resume has been retained."
            ),
            "warning": (
                "The optimizer did not return a safe improvement. "
                "Original resume was returned to avoid adding fake or unsupported skills."
            ),
            **comparison_result
        }

    improvement = best_score - original_score

    logger.info(
        f"Final optimized score selected. Original={original_score}, "
        f"Optimized={best_score}, Improvement={improvement}"
    )

    comparison_result = create_comparison_result(
        job_requirement_text=job_requirement_text,
        original_resume=resume_text,
        optimized_resume=best_resume,
        original_score=original_score,
        optimized_score=best_score
    )

    return {
        "original_match_percentage": original_score,
        "optimized_match_percentage": best_score,
        "improvement_percentage": improvement,
        "optimized_resume": best_resume,
        "added_or_improved_keywords": best_result.get("added_or_improved_keywords", []),
        "not_added_keywords": best_result.get("not_added_keywords", []),
        "changes_summary": best_result.get("changes_summary", ""),
        "warning": best_result.get(
            "warning",
            "Resume optimized without adding unsupported skills or fake experience."
        ),
        **comparison_result
    }