from pydantic import BaseModel, Field
from typing import List, Dict, Any


class ResumeAnalysisResponse(BaseModel):
    final_match_percentage: int
    llm_match_percentage: int
    embedding_similarity_percentage: int
    matched_skills: List[str]
    partially_matched_skills: List[str]
    missing_skills: List[str]
    summary: str
    recommendation: str


class ResumeOptimizationResponse(BaseModel):
    original_match_percentage: int
    optimized_match_percentage: int
    improvement_percentage: int
    optimized_resume: str
    added_or_improved_keywords: List[str]
    not_added_keywords: List[str]
    changes_summary: str
    warning: str

    original_professional_summary: str = ""
    optimized_professional_summary: str = ""
    original_technical_skills: List[str] = Field(default_factory=list)
    optimized_technical_skills: List[str] = Field(default_factory=list)
    technical_skill_comparison: List[Dict[str, Any]] = Field(default_factory=list)

    comparison_data: Dict[str, Any] = Field(default_factory=dict)