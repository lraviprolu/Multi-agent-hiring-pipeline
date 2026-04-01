from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CandidateProfile:
    name: str
    email: str
    phone: str
    years_of_experience: float
    skills: List[str]
    education: str
    previous_roles: List[str]
    summary: str


@dataclass
class MatchResult:
    score: float                  # 0–100
    matched_skills: List[str]
    missing_skills: List[str]
    reasoning: str


@dataclass
class InterviewPlan:
    candidate_name: str
    questions: List[str]


@dataclass
class GapReport:
    candidate_name: str
    match_score: float
    missing_skills: List[str]
    recommendations: str
