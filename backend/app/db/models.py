
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, Float, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .session import Base

class Resume(Base):
    """
    The central entity. 
    We store the 'raw_text' permanently so we can re-run section detection logic 
    later if we improve our algorithms, without asking the user to re-upload.
    """
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False) # Placeholder for auth wrapper
    file_path = Column(String, nullable=False)
    
    # Critical: This is the Source of Truth. If parsing fails, we fallback to this.
    raw_text = Column(Text, nullable=False)
    
    # Store the output of our heuristic parser (Step 2.4) so we don't re-compute on every read.
    parsed_json = Column(JSONB, nullable=True) 
    
    # Quick flag to filter "ready" resumes from "processing/failed" ones
    is_parsed = Column(Boolean, default=False) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JobDescription(Base):
    """
    Simple storage for JDs. 
    In the future, we might want to parsed these into sections too, 
    but for now, raw text is sufficient for embeddings.
    """
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    raw_text = Column(Text, nullable=False)
    # Added parsed_json to store detected sections (Responsibilities, Requirements, etc)
    parsed_json = Column(JSONB, nullable=True)
    # Extracted Experience Requirement (Step 4.5)
    min_years_experience = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SkillCategory(str, enum.Enum):
    language = "language"
    framework = "framework"
    tool = "tool"
    concept = "concept"

class SkillsMaster(Base):
    """
    The 'controlled vocabulary' for skills. 
    We use this to normalize 'React.js', 'ReactJS', and 'React' into a single ID.
    This prevents the AI from hallucinating slight variations of the same skill.
    """
    __tablename__ = "skills_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(SQLAlchemyEnum(SkillCategory), nullable=False)

class ResumeSkill(Base):
    """
    Junction table linking a Resume to a normalized Skill.
    'confidence_score' allows us to flag skills that were inferred vs explicitly stated.
    """
    __tablename__ = "resume_skills"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    skill_id = Column(Integer, ForeignKey("skills_master.id"))
    confidence_score = Column(Float, nullable=False)
    evidence_text = Column(Text, nullable=True) # The exact snippet where we found this

class JDSkillImportance(str, enum.Enum):
    critical = "critical"
    optional = "optional"

class JDSkill(Base):
    """
    Skills extracted from a JD.
    Distinguishing 'critical' vs 'optional' is key for the weighted scoring algorithm.
    """
    __tablename__ = "jd_skills"

    id = Column(Integer, primary_key=True, index=True)
    jd_id = Column(Integer, ForeignKey("job_descriptions.id"))
    skill_id = Column(Integer, ForeignKey("skills_master.id"))
    importance = Column(SQLAlchemyEnum(JDSkillImportance), nullable=False)

class AnalysisResult(Base):
    """
    An immutable snapshot of a match attempt.
    If we change the scoring algorithm, we create a NEW result, we don't update old ones.
    """
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    jd_id = Column(Integer, ForeignKey("job_descriptions.id"))
    overall_match_score = Column(Float)
    
    # Stores the full detailed breakdown (missing skills, gap analysis) 
    # to avoid complex joins when just displaying the report card.
    result_json = Column(JSONB, nullable=False) 
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
