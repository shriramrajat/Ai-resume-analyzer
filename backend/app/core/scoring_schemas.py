
from typing import List, Dict, Optional
from pydantic import BaseModel

# Input Data Structures (Pure data, no ORM objects passed deeply)

class SkillMatchInput(BaseModel):
    skill_id: int
    skill_name: str
    context_confidence: float # From Resume (0.0 - 1.0)
    
class JDSkillRequirement(BaseModel):
    skill_id: int
    skill_name: str
    importance: str # 'critical' or 'optional'

class ScoringConfiguration(BaseModel):
    critical_weight: float = 2.0
    optional_weight: float = 1.0
    experience_weight: float = 0.5 # Impact of years gap

class MatchInput(BaseModel):
    resume_skills: List[SkillMatchInput]
    jd_skills: List[JDSkillRequirement]
    
    resume_experience_years: int
    jd_experience_years: int
