
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Resume, JobDescription, ResumeSkill, JDSkill, AnalysisResult
from app.services.matching_engine import (
    evaluate_skill_gap, 
    calculate_skill_score, 
    calculate_experience_match,
    calculate_risk_flags,
    calculate_final_score
)
from app.core.scoring_schemas import MatchInput, SkillMatchInput, JDSkillRequirement
from typing import Dict
from pydantic import BaseModel

router = APIRouter()

class AnalyzeRequest(BaseModel):
    resume_id: int
    jd_id: int

@router.post("/analyze")
async def analyze_match(
    request: AnalyzeRequest, 
    db: Session = Depends(get_db)
):
    # 1. Fetch Resources
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    jd = db.query(JobDescription).filter(JobDescription.id == request.jd_id).first()
    
    if not resume or not jd:
        raise HTTPException(status_code=404, detail="Resume or JD not found")
        
    # 2. Fetch Structured Data (The Inputs)
    # Resume Skills
    r_skills = db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).all()
    # JD Skills
    j_skills = db.query(JDSkill).filter(JDSkill.jd_id == jd.id).all()
    
    # 3. Transform to Input Schema (Decouple from ORM)
    input_r_skills = []
    # Need to join with SkillsMaster to get names? 
    # Yes, optimization: fetch names or eager load.
    # For now, simple query iteration is OK for small data.
    from app.db.models import SkillsMaster
    
    # Create Name Map for fast lookup
    all_skill_names = {s.id: s.name for s in db.query(SkillsMaster).all()}
    
    for rs in r_skills:
        input_r_skills.append(SkillMatchInput(
            skill_id=rs.skill_id,
            skill_name=all_skill_names.get(rs.skill_id, "Unknown"),
            context_confidence=rs.confidence_score
        ))
        
    input_j_skills = []
    for js in j_skills:
        input_j_skills.append(JDSkillRequirement(
            skill_id=js.skill_id,
            skill_name=all_skill_names.get(js.skill_id, "Unknown"),
            importance=js.importance.value
        ))
        
    # Get Experience (Naive for now)
    # Step 4.5 logic saved min_years_experience
    # Resume experience? We need to calculate 'actual_years'.
    # For now, let's parse it from parsed_json or assume 0 if not calculated yet.
    # TODO: Resume Experience Extraction was not explicitly built as a service in Phase 2?
    # Phase 2.4 detected sections but not explicit years.
    # I will reuse 'extract_experience_requirements' logic on Resume Experience section!
    
    from app.services.experience_extractor import extract_years_of_experience
    resume_exp_text = resume.parsed_json.get('experience', '') if resume.parsed_json else ""
    actual_years = extract_years_of_experience(resume_exp_text) or 0
    
    match_input = MatchInput(
        resume_skills=input_r_skills,
        jd_skills=input_j_skills,
        resume_experience_years=actual_years,
        jd_experience_years=jd.min_years_experience
    )
    
    # 4. Run Matching Engine
    skill_gap = evaluate_skill_gap(match_input)
    skill_score = calculate_skill_score(skill_gap)
    
    exp_analysis = calculate_experience_match(actual_years, jd.min_years_experience)
    
    risks = calculate_risk_flags(skill_gap, exp_analysis)
    
    final_score = calculate_final_score(skill_score, exp_analysis['penalty_factor'])
    
    # 5. Persist Result (Step 5.7)
    # Formatting to Strict Output Structure (Step 5.8)
    
    formatted_skill_analysis = {
        "matched": [m['skill_name'] for m in skill_gap['matched']],
        "missing_critical": [m['skill_name'] for m in skill_gap['missing_critical']],
        "missing_optional": [m['skill_name'] for m in skill_gap['missing_optional']]
    }
    
    # Simple Rule-based Strengths (Facts) based on high confidence matches
    strengths = []
    for m in skill_gap['matched']:
        if m['importance'] == 'critical':
             strengths.append(f"Matched Critical Skill: {m['skill_name']}")

    result_json = {
        "overall_match_score": final_score,
        "skill_analysis": formatted_skill_analysis,
        "experience_analysis": {
            "required_years": exp_analysis['required_years'],
            "actual_years": exp_analysis['actual_years'],
            "gap": exp_analysis['gap']
        },
        "strengths": strengths, 
        "risks": risks,
        "recommendations": [] # To be filled by AI Explanation Layer in Phase 6
    }
    
    analysis_record = AnalysisResult(
        resume_id=resume.id,
        jd_id=jd.id,
        overall_match_score=final_score,
        result_json=result_blob # Save internal detailed blob? OR strict output?
        # Ideally we save the detailed one for debugging, but the prompt says 5.8 IS the output.
        # Let's save the Strict Output.
        result_json=result_json 
    )
    
    db.add(analysis_record)
    db.commit()
    db.refresh(analysis_record)
    
    return result_json
