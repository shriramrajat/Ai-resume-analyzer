
from sqlalchemy.orm import Session
from app.db.models import SkillsMaster, Resume, ResumeSkill
from app.services.parser_rules import detect_sections
import json

# This service implements the logic of "What is a Skill"
# It does NOT just keyword match. It weights evidence based on SECTION.

def extract_skills_with_evidence(resume: Resume, db: Session):
    """
    Extracts skills from a resume by mapping text to the SkillsMaster ontology.
    
    Rule-Based Confidence Scoring:
    1. Found in 'Experience'/'Projects' context -> High Confidence (0.8 - 1.0)
       Why: Usage implies actual experience.
    2. Found in 'Skills' list -> Medium Confidence (0.5)
       Why: It's just a claim, no proof of depth.
    3. Found in 'Education' -> Low Confidence (0.3)
       Why: Academic exposure != production skill.
       
    This is deterministic. AI is ONLY used (later) to normalize tricky phrasing 
    if this strict lookup fails. For now, strict lookup against Ontology.
    """
    
    # 1. Load the Ontology (Controlled Vocabulary)
    all_skills = db.query(SkillsMaster).all()
    # Create lookup map: lowercase name -> skill obj
    skill_map = {s.name.lower(): s for s in all_skills}
    
    # 2. Get Parsed Sections (already done in Step 2.4)
    # If not present, re-parse (fallback)
    sections = resume.parsed_json
    if not sections:
        from app.services.parser_rules import detect_sections
        sections = detect_sections(resume.raw_text)
    
    detected_skills = {} # skill_id -> {confidence, evidence, skill_name}

    # 3. Iterate through sections with weighted importance
    # Priority order: Experience > Projects > Skills > Education
    
    # 3. Iterate through sections with weighted importance
    # Priority order: Experience > Projects > Skills > Education
    
    section_weights = {
        "experience": 0.9,
        "projects": 0.8,
        "skills": 0.5, # Just a list of keywords
        "education": 0.3,
        "uncategorized": 0.2
    }
    
    # Track cross-section accumulation
    # skill_id -> { 'sections': set(), 'count': 0, 'evidence': ... }
    skill_acc = {}

    for section_name, text_content in sections.items():
        if not text_content:
            continue
            
        weight = section_weights.get(section_name, 0.2)
        text_lower = text_content.lower()
        
        for name, skill_obj in skill_map.items():
            # Check presence
            if name in text_lower:
                # Basic Evidence
                idx = text_lower.find(name)
                start = max(0, idx - 40)
                end = min(len(text_content), idx + 40)
                evidence = "..." + text_content[start:end].replace('\n', ' ') + "..."
                
                # Count occurrences in this text to simulate "mulitple roles"
                # (Simple proxy: if word appears > 2 times in Experience, likely used in multiple places)
                count = text_lower.count(name)
                
                sid = skill_obj.id
                if sid not in skill_acc:
                    skill_acc[sid] = {
                        "base_score": 0.0,
                        "sections": set(),
                        "evidence": evidence, # Keep first found evidence
                        "total_count": 0
                    }
                
                # Update stats
                skill_acc[sid]['sections'].add(section_name)
                skill_acc[sid]['total_count'] += count
                # Keep strongest section base score
                if weight > skill_acc[sid]['base_score']:
                    skill_acc[sid]['base_score'] = weight
                    skill_acc[sid]['evidence'] = evidence

    # Final Score Calculation
    detected_skills = {}
    
    for sid, data in skill_acc.items():
        sk_obj = next(s for s in all_skills if s.id == sid)
        
        final_score = data['base_score']
        
        # Rule: Appears in Project + Experience -> Boost
        if 'experience' in data['sections'] and 'projects' in data['sections']:
            final_score = 0.9 # Cap at 0.9 (Very high)
        elif len(data['sections']) > 1:
            # Found in multiple sections (e.g. Skills + Experience)
            final_score = min(1.0, final_score + 0.1)
            
        # Rule: Appears multiple times in Experience (proxy for "multiple roles")
        if 'experience' in data['sections'] and data['total_count'] >= 3:
             final_score = min(1.0, final_score + 0.1) # Boost for frequency
             
        detected_skills[sid] = {
            "confidence": round(final_score, 2),
            "evidence": data['evidence'],
            "skill_name": sk_obj.name
        }

    # 4. Store Results in DB
    # Clear old skills for this resume first (if re-running)
    db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).delete()
    
    new_skills = []
    for skill_id, data in detected_skills.items():
        new_skills.append(ResumeSkill(
            resume_id=resume.id,
            skill_id=skill_id,
            confidence_score=data['confidence'],
            evidence_text=data['evidence']
        ))
    
    
    if new_skills:
        db.bulk_save_objects(new_skills)
        db.commit()
        
    return detected_skills

def extract_skills_hybrid(resume: Resume, db: Session):
    """
    Orchestrates the hybrid extraction:
    1. Deterministic (Exact Match) - FAST, HIGH PRECISION, ZERO COST.
    2. AI-Assisted (Semantic Match) - SLOW, COSTLY, HANDLES NUANCE.
    
    Strategy:
    - Run deterministic first.
    - (Optional) Run AI on 'Experience' section to catch implicit skills 
      ONLY IF mapped to Ontology.
    """
    # 1. Run Rule-Based
    deterministic_matches = extract_skills_with_evidence(resume, db)
    
    # 2. AI Extraction (Step 3.3)
    # Only run on Experience/Projects to save tokens and avoid noise
    # This part requires an LLM Client (not yet verified configured)
    # So we structure it but maybe don't block on it yet.
    
    # from app.services.llm_service import query_llm_for_skills
    # allowed_skills = [s.name for s in db.query(SkillsMaster).all()]
    # ai_matches = query_llm_for_skills(resume.parsed_json.get('experience', ''), allowed_skills)
    
    # 3. Merge Logic would go here
    # Priority: Deterministic matches are usually safer for strict keywords.
    # AI is good for "I used Django-like patterns" -> "Django" (maybe)
    
    return deterministic_matches
