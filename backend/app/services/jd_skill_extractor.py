
from sqlalchemy.orm import Session
from app.db.models import JobDescription, SkillsMaster, JDSkill, JDSkillImportance
from app.services.llm_service import query_llm_for_jd_skills
import json

def extract_jd_skills(jd: JobDescription, db: Session):
    """
    Extracts skills from JD using a Hybrid Approach:
    1. Heuristic: If we find it in "Must Haves", marker is critical.
    2. AI: We allow AI to parse the nuance of "Preferred" vs "Required".
    
    For now, relying on the 'query_llm_for_jd_skills' contract.
    Since AI key might be missing, we will implement a fallback heuristic 
    similar to Resume extraction to ensure the system works logically without AI.
    """
    
    all_skills = db.query(SkillsMaster).all()
    skill_map = {s.name.lower(): s for s in all_skills}
    
    sections = jd.parsed_json
    if not sections:
        return []

    # Heuristic Fallback / Pre-processing
    found_skills = {} # skill_name -> importance
    
    # Helper to refine importance based on nearby keywords (Step 4.4)
    def determine_importance(text_segment: str, basic_importance: str) -> str:
        text_lower = text_segment.lower()
        # Heuristic Enforcement: Override based on strong cues
        if any(x in text_lower for x in ["nice to have", "plus", "bonus", "preferred", "good to have"]):
            return "optional"
        if any(x in text_lower for x in ["must", "required", "essential", "minimum", "proficiency in"]):
            return "critical"
        return basic_importance

    # 1. Process 'Requirements' section
    req_text = sections.get('requirements', '').lower()
    for name, skill_obj in skill_map.items():
        if name in req_text:
            # Check Evidence Snippet for overriding keywords
            idx = req_text.find(name)
            start = max(0, idx - 40)
            end = min(len(req_text), idx + 40)
            snippet = req_text[start:end]
            
            # Default to critical in requirements, but check for "nice to have" inline
            importance = determine_importance(snippet, "critical")
            found_skills[skill_obj.id] = importance
            
    # 2. Process 'Nice to Have' section
    nice_text = sections.get('nice_to_have', '').lower()
    for name, skill_obj in skill_map.items():
        if name in nice_text:
            # Almost certainly optional, unless they wrote "Must know Python" in the nice-to-have section (unlikely)
            found_skills[skill_obj.id] = "optional"
    
    # 3. Process 'Responsibilities'
    resp_text = sections.get('responsibilities', '').lower()
    for name, skill_obj in skill_map.items():
        if name in resp_text and skill_obj.id not in found_skills:
             snippet_idx = resp_text.find(name)
             snippet = resp_text[max(0, snippet_idx - 30): min(len(resp_text), snippet_idx + 30)]
             
             importance = determine_importance(snippet, "critical")
             found_skills[skill_obj.id] = importance
             
    # 4. (Hybrid) AI Refinement Layer
    # Use AI to double-check importance or find context-heavy skills we missed,
    # but ONLY if they are in the allowed list.
    try:
        from app.core.config import settings
        if settings.OPENAI_API_KEY:
             # We pass the Raw Text or the combined sections
             full_text = jd.raw_text[:4000] # Truncate to avoid context limits if massively long
             allowed_names = [s.name for s in all_skills]
             
             ai_results = query_llm_for_jd_skills(full_text, allowed_names)
             
             for item in ai_results:
                 s_name = item.get("skill", "").lower()
                 s_imp = item.get("importance", "critical").lower()
                 
                 if s_name in skill_map:
                     s_id = skill_map[s_name].id
                     # Strategy: Upsert
                     # If AI says it's there, we trust it exists.
                     # If AI says Critical, we trust it over Heuristic "Optional" (unless context is super weird)
                     found_skills[s_id] = s_imp
    except Exception as e:
        print(f"AI Extraction Skipped/Failed: {e}")
    
    # Persist
    db.query(JDSkill).filter(JDSkill.jd_id == jd.id).delete()
    
    new_entries = []
    for sid, importance_str in found_skills.items():
        new_entries.append(JDSkill(
            jd_id=jd.id,
            skill_id=sid,
            importance=JDSkillImportance(importance_str)
        ))
        
    if new_entries:
        db.bulk_save_objects(new_entries)
        db.commit()
    
    return found_skills
