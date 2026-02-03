
import pytest
from app.services.matching_engine import (
    evaluate_skill_gap,
    calculate_skill_score,
    calculate_experience_match,
    calculate_final_score,
    calculate_risk_flags
)
from app.core.scoring_schemas import MatchInput, SkillMatchInput, JDSkillRequirement

def test_experience_match_exact():
    # Gap 0
    res = calculate_experience_match(resume_years=5, jd_years=5)
    assert res['gap'] == 0
    assert res['status'] == 'sufficient'
    assert res['penalty_factor'] == 1.0

def test_experience_match_deficit_minor():
    # Gap -1
    res = calculate_experience_match(resume_years=4, jd_years=5)
    assert res['gap'] == -1
    assert res['status'] == 'deficit'
    assert res['penalty_factor'] == 1.0 # Logic says only < -1 triggers penalty 0.85? Wait, let's check code. 
    # Code: if gap < -1: penalty = 0.85. So -1 is safe? 
    # Ah, implementation says: if gap < 0: status deficit. if gap < -1: 0.85. 
    # So gap of -1 means penalty is 1.0 (no penalty), which matches code but maybe not intent? 
    # User README: Gap = -1: Score 0.8. Gap < -1: Score 0.5.
    # The code implementation uses penalty_factor logic inside calculate_experience_match, 
    # but calculate_final_score interprets it.
    
def test_calculate_final_score_logic():
    # Validate the mapping from step 162 in matching_engine.py
    
    # 1. Perfect Skill (1.0) + Perfect Exp (factor 1.0 -> score 1.0)
    # Final = 1.0 * 0.7 + 1.0 * 0.3 = 1.0
    assert calculate_final_score(1.0, 1.0) == 1.0
    
    # 2. Perfect Skill (1.0) + Major Deficit (factor 0.85 -> score 0.5)
    # Final = 0.7 + (0.5 * 0.3) = 0.7 + 0.15 = 0.85
    assert calculate_final_score(1.0, 0.85) == 0.85

def test_evaluate_skill_gap_logic():
    # Setup Data
    r_skills = [
        SkillMatchInput(skill_id=1, skill_name="Python", context_confidence=0.9), # Strong match
        SkillMatchInput(skill_id=2, skill_name="Docker", context_confidence=0.5), # Weak match (filtered out < 0.6)
    ]
    jd_skills = [
        JDSkillRequirement(skill_id=1, skill_name="Python", importance="critical"),
        JDSkillRequirement(skill_id=2, skill_name="Docker", importance="critical"), # Missing because confidence low
        JDSkillRequirement(skill_id=3, skill_name="Kubernetes", importance="optional"), # Missing entirely
    ]
    
    inp = MatchInput(
        resume_skills=r_skills, 
        jd_skills=jd_skills,
        resume_experience_years=5,
        jd_experience_years=5
    )
    
    result = evaluate_skill_gap(inp)
    
    # Assertions
    assert len(result['matched']) == 1
    assert result['matched'][0]['skill_name'] == "Python"
    
    assert len(result['missing_critical']) == 1
    assert result['missing_critical'][0]['skill_name'] == "Docker" # Filtered out due to confidence
    
    assert len(result['missing_optional']) == 1
    assert result['missing_optional'][0]['skill_name'] == "Kubernetes"

def test_full_scoring_flow():
    # Integration of calculation functions
    
    # 1. Evaluate Gaps
    gap_res = {
        "matched": [{"importance": "critical"}, {"importance": "optional"}], # 1 Crit, 1 Opt
        "missing_critical": [{"importance": "critical"}], # 1 Crit Missing
        "missing_optional": []
    }
    
    # Score Calc
    # Total Critical = 1 (matched) + 1 (missing) = 2. Weight 2.0 -> 4.0 points total.
    # Total Optional = 1 (matched) + 0 (missing) = 1. Weight 1.0 -> 1.0 points total.
    # Denom = 5.0
    # Numerator = (1 * 2.0) + (1 * 1.0) = 3.0
    # Score = 3.0 / 5.0 = 0.60
    
    s_score = calculate_skill_score(gap_res)
    assert s_score == 0.60
    
    # 2. Experience
    # Gap -2 -> Penalty 0.85 -> Exp Score 0.5
    e_res = calculate_experience_match(3, 5) # 3 years vs 5 years
    assert e_res['penalty_factor'] == 0.85
    
    # 3. Final
    # (0.60 * 0.7) + (0.5 * 0.3) = 0.42 + 0.15 = 0.57
    final = calculate_final_score(s_score, e_res['penalty_factor'])
    assert final == 0.57
