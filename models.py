# models.py - No openenv dependency

from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class ResumeAction(BaseModel):
    """Action for the Resume Screening environment."""
    
    decision: Literal["shortlist", "reject", "hold"] = Field(
        ..., 
        description="Decision on the candidate: shortlist, reject, or hold"
    )


class ResumeObservation(BaseModel):
    """Observation from the Resume Screening environment."""
    
    candidate_id: str = Field(..., description="Unique identifier for the candidate")
    target_role: Literal["junior", "mid", "senior"] = Field(
        ..., 
        description="Target job role: junior, mid, or senior engineer"
    )
    education: str = Field(..., description="Candidate's educational background")
    experience_years: float = Field(..., description="Years of professional experience")
    skills: List[str] = Field(..., description="List of technical skills")
    projects: List[str] = Field(..., description="List of projects")
    certifications: Optional[List[str]] = Field(
        default=None, 
        description="Optional list of certifications"
    )
    gap_years: float = Field(
        default=0.0, 
        description="Number of years with career gaps"
    )
    ground_truth_decision: Optional[str] = Field(
        default=None, 
        description="Ground truth decision for evaluation"
    )
    done: bool = Field(default=False, description="Whether the episode is done")
    reward: float = Field(default=0.0, description="Reward for the last action")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
