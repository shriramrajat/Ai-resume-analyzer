from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Resume, JobDescription, ResumeSkill, JDSkill, AnalysisResult, AnalysisExplanation
from app.services.matching_engine import (
    evaluate_skill_gap, 
    calculate_skill_score, 
    calculate_experience_match,
    calculate_risk_flags,
    calculate_final_score
)
from app.core.scoring_schemas import MatchInput, SkillMatchInput, JDSkillRequirement
from app.services.llm_service import generate_ai_explanation
from typing import Dict
from pydantic import BaseModel

router = APIRouter()

class AnalyzeRequest(BaseModel):
    resume_id: int
    jd_id: int

def process_analysis_task(analysis_id: int, resume_id: int, jd_id: int, db: Session):
    """
    Background Task: Encapsulates the heavy lifting (Step 5 & 6).
    """
    try:
        # Re-fetch objects in this thread/session context
        resume = db.query(Resume).filter(Resume.id == resume_id).first()
        jd = db.query(JobDescription).filter(JobDescription.id == jd_id).first()
        analysis = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
        
        if not resume or not jd or not analysis:
            return 

        # --- MATCHING ENGINE LOGIC (Step 5) ---
        r_skills = db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).all()
        j_skills = db.query(JDSkill).filter(JDSkill.jd_id == jd.id).all()
        
        from app.db.models import SkillsMaster
        all_skill_names = {s.id: s.name for s in db.query(SkillsMaster).all()}
        
        input_r_skills = [
            SkillMatchInput(skill_id=rs.skill_id, skill_name=all_skill_names.get(rs.skill_id, "Unknown"), context_confidence=rs.confidence_score)
            for rs in r_skills
        ]
        input_j_skills = [
            JDSkillRequirement(skill_id=js.skill_id, skill_name=all_skill_names.get(js.skill_id, "Unknown"), importance=js.importance.value)
            for js in j_skills
        ]
        
        from app.services.experience_extractor import extract_years_of_experience
        resume_exp_text = resume.parsed_json.get('experience', '') if resume.parsed_json else ""
        actual_years = extract_years_of_experience(resume_exp_text) or 0
        
        match_input = MatchInput(
            resume_skills=input_r_skills,
            jd_skills=input_j_skills,
            resume_experience_years=actual_years,
            jd_experience_years=jd.min_years_experience
        )
        
        skill_gap = evaluate_skill_gap(match_input)
        skill_score = calculate_skill_score(skill_gap)
        exp_analysis = calculate_experience_match(actual_years, jd.min_years_experience)
        risks = calculate_risk_flags(skill_gap, exp_analysis)
        final_score = calculate_final_score(skill_score, exp_analysis['penalty_factor'])
        
        # Format Results
        formatted_skill_analysis = {
            "matched": [m['skill_name'] for m in skill_gap['matched']],
            "missing_critical": [m['skill_name'] for m in skill_gap['missing_critical']],
            "missing_optional": [m['skill_name'] for m in skill_gap['missing_optional']]
        }
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
            "recommendations": []
        }
        
        # --- TRANSPARENCY METADATA (Step 7.5) ---
        # Logic to determine system confidence in ITSELF
        system_confidence = "high"
        limitations = ["Automated analysis based on keyword matching and heuristics."]
        
        if not skill_gap['matched'] and not skill_gap['missing_critical']:
             # Weird case: no skills found?
             system_confidence = "low"
             limitations.append("No technical skills detected in JD or Resume.")
        elif actual_years == 0 and jd.min_years_experience > 0:
             # Possible parse fail on resume experience?
             system_confidence = "medium"
             limitations.append("Could not confidently extract experience years from resume.")
             
        analysis_metadata = {
            "confidence_level": system_confidence,
            "limitations": limitations
        }
        
        # --- AI GENERATION LOGIC (Step 6) ---
        explanation_data = generate_ai_explanation(result_json)
        explanation_record = AnalysisExplanation(
            analysis_id=analysis.id,
            explanation_json=explanation_data
        )
        db.add(explanation_record)
        
        # Update Analysis Record
        analysis.overall_match_score = final_score
        analysis.result_json = result_json
        analysis.analysis_metadata = analysis_metadata # Added 7.5
        analysis.status = "completed"
        
        db.commit()
        
    except Exception as e:
        print(f"Analysis Failed: {e}")
        # Ideally capture error in DB
        analysis = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
        if analysis:
            analysis.status = "failed"
            db.commit()


@router.post("") # POST /api/v1/analysis
async def start_analysis(
    request: AnalyzeRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    print(f"Received analysis request: resume_id={request.resume_id}, jd_id={request.jd_id}")
    try:
        # Create the record immediately (Pending State)
        new_analysis = AnalysisResult(
            resume_id=request.resume_id,
            jd_id=request.jd_id,
            status="processing",
            overall_match_score=0.0,
            result_json={},
            engine_version="1.0.0" # Versioning Step 7.4
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        
        # Hand off to background task
        background_tasks.add_task(process_analysis_task, new_analysis.id, request.resume_id, request.jd_id, db)
        
        return {
            "analysis_id": new_analysis.id,
            "status": "processing"
        }
    except Exception as e:
        print(f"ERROR in start_analysis: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{analysis_id}")
async def get_analysis_result(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    analysis = db.query(AnalysisResult).filter(AnalysisResult.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
        
    explanation = db.query(AnalysisExplanation).filter(AnalysisExplanation.analysis_id == analysis.id).first()
    
    return {
        "analysis": {
            "id": analysis.id,
            "status": analysis.status,
            "score": analysis.overall_match_score,
            "details": analysis.result_json,
            "created_at": analysis.created_at
        },
        "explanation": explanation.explanation_json if explanation else None
    }
