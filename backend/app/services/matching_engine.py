
from typing import List, Dict
from app.core.scoring_schemas import MatchInput, SkillMatchInput, JDSkillRequirement

# Constants
MIN_CONFIDENCE_THRESHOLD = 0.6  # Mentioning != Knowing

def evaluate_skill_gap(input_data: MatchInput) -> Dict:
    """
    Performs the core intersection of Resume Skills vs JD Skills.
    
    Logic:
    1. Filter Resume Skills by Confidence Threshold (>= 0.6).
    2. Check JD Critical Skills: Are they in the valid resume list?
    3. Check JD Optional Skills: Are they in the valid resume list?
    
    Returns:
        Dict partitioned into: 'matched', 'missing_critical', 'missing_optional'
    """
    
    # 1. Prepare Valid Resume Skills Map (id -> data)
    # We drop any skill with confidence < 0.6
    
    valid_resume_skills = {}
    for r_skill in input_data.resume_skills:
        if r_skill.context_confidence >= MIN_CONFIDENCE_THRESHOLD:
            valid_resume_skills[r_skill.skill_id] = r_skill
            
    # 2. Iterate JD Constraints
    
    results = {
        "matched": [],
        "missing_critical": [],
        "missing_optional": []
    }
    
    for req in input_data.jd_skills:
        skill_id = req.skill_id
        
        is_matched = skill_id in valid_resume_skills
        
        match_detail = {
            "skill_id": skill_id,
            "skill_name": req.skill_name,
            "importance": req.importance
        }
        
        if is_matched:
            # Add confidence context to the result for transparency
            r_skill = valid_resume_skills[skill_id]
            match_detail["resume_confidence"] = r_skill.context_confidence
            results["matched"].append(match_detail)
        else:
            if req.importance == "critical":
                results["missing_critical"].append(match_detail)
            else:
                results["missing_optional"].append(match_detail)
                
    return results

def calculate_skill_score(gap_results: Dict) -> float:
    """
    Computes the weighted score (0.0 - 1.0) based on critical/optional matches.
    
    Formula:
        (matched_crit * W_CRIT + matched_opt * W_OPT) / TOTAL_POSSIBLE_SCORE
    """
    CRITICAL_WEIGHT = 2.0
    OPTIONAL_WEIGHT = 1.0
    
    # Count matches by type
    matched_crit_count = 0
    matched_opt_count = 0
    
    for m in gap_results["matched"]:
        if m["importance"] == "critical":
            matched_crit_count += 1
        else:
            matched_opt_count += 1
            
    # Count missing
    missing_crit_count = len(gap_results["missing_critical"])
    missing_opt_count = len(gap_results["missing_optional"])
    
    # Totals
    total_critical = matched_crit_count + missing_crit_count
    total_optional = matched_opt_count + missing_opt_count
    
    if total_critical == 0 and total_optional == 0:
        return 0.0 # No requirements? Baseline 0 or 1? Usually 0 if nothing to match against.
        
    numerator = (matched_crit_count * CRITICAL_WEIGHT) + (matched_opt_count * OPTIONAL_WEIGHT)
    denominator = (total_critical * CRITICAL_WEIGHT) + (total_optional * OPTIONAL_WEIGHT)
    
    if denominator == 0:
        return 0.0
        
    return round(numerator / denominator, 2)

def calculate_experience_match(resume_years: int, jd_years: int) -> Dict:
    """
    Computes experience gap and penalty factor.
    
    Logic:
    - Gap = actual - required
    - If gap < -1 (more than 1 year deficit): Apply Penalty.
    - Penalty: Reduce final score by 15% (factor 0.85).
    """
    gap = resume_years - jd_years
    
    penalty_factor = 1.0
    status = "sufficient"
    
    if gap < 0:
        status = "deficit"
        if gap < -1:
            # Significant mismatch (> 1 year missing)
            # Apply 15% penalty to the total score.
            penalty_factor = 0.85
            
    return {
        "required_years": jd_years,
        "actual_years": resume_years,
        "gap": gap,
        "status": status,
        "penalty_factor": penalty_factor
    }

def calculate_risk_flags(gap_results: Dict, exp_analysis: Dict) -> List[str]:
    """
    Generates rule-based flags for "Why you might be rejected".
    Interpretation, not just math.
    """
    risks = []
    
    # 1. Critical Skill Gaps
    missing_crit = gap_results["missing_critical"]
    if len(missing_crit) > 0:
        count = len(missing_crit)
        names = ", ".join([m['skill_name'] for m in missing_crit[:3]])
        risks.append(f"Missing {count} Critical Skills ({names})")
        
    # 2. Experience Gap
    gap = exp_analysis['gap']
    if gap < -2:
        risks.append(f"Severe Experience Deficit ({gap} years)")
    elif gap < 0:
        risks.append(f"Experience Gap ({gap} years)")
        
    # 3. Weak Evidence for Critical Matches
    # (If we matched a critical skill, but confidence was barely above threshold? 
    # Or if confidence was high but we treat it differently? 
    # Current engine filters < 0.6 already, so matches are at least 0.6.
    # But maybe 0.6 is still 'weak' compared to 0.9)
    
    for m in gap_results['matched']:
        if m['importance'] == 'critical' and m['resume_confidence'] < 0.7:
             risks.append(f"Low Confidence in Critical Skill: {m['skill_name']} ({m['resume_confidence']})")
             
    return risks

def calculate_final_score(skill_score: float, penalty_factor: float) -> float:
    """
    Combines Skill Score and Experience Penalty into Final Score.
    
    Formula:
        Base = (Skill Score * 1.0) 
        # Wait, Step 5.6 says: skill_score * 0.7 + exp_score * 0.3
        # But my experience logic returned a PENALTY factor, not a raw 0-1 score yet.
        # Let's adapt to constraints:
        # If experience is penalized, it drags down the score.
        # If experience is perfect, it adds 30%.
        
    Revised Logic per Request:
    - We need an 'experience_score'.
    - If Penalty Factor is 1.0 (OK) -> Exp Score = 1.0
    - If Penalty Factor is 0.85 (Deficit) -> Exp Score = 0.5? 
    - Let's derive a numeric 'experience_score' from the gap logic:
      - Gap >= 0: 1.0
      - Gap -1: 0.8
      - Gap -2: 0.5
      - Gap -3: 0.2
    
    Then apply: Final = (Skill * 0.7) + (Exp * 0.3)
    """
    # Assuming the penalty_factor passed in was the rough proxy.
    # Let's reconstruct an exp_score.
    
    exp_score = 1.0
    if penalty_factor < 1.0:
        # If we had a penalty, it maps to a lower score
        if penalty_factor == 0.85: # Gap < -1
            exp_score = 0.5 # Severe hit
        else:
            exp_score = 0.8 # Minor hit
            
    final = (skill_score * 0.7) + (exp_score * 0.3)
    
    return round(final, 2)
