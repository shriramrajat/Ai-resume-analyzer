
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import JobDescription

router = APIRouter()

class JDCreateRequest(BaseModel):
    # Expecting raw text directly mostly, as JDs are often copy-pasted.
    # If the user wants to upload a PDF for JD, that's fine too, but 
    # instructions imply "Store raw JD text".
    raw_text: str

@router.post("/create")
async def create_jd(
    request: JDCreateRequest, 
    db: Session = Depends(get_db)
):
    if not request.raw_text.strip():
        raise HTTPException(status_code=400, detail="JD text cannot be empty")
        
    # Text Normalization (Standardize inputs)
    from app.core.text_utils import normalize_text
    normalized_text = normalize_text(request.raw_text)
    
    # Section Detection (Step 4.2)
    from app.services.parser_rules import detect_jd_sections
    sections = detect_jd_sections(normalized_text)
        
    new_jd = JobDescription(
        raw_text=request.raw_text, # Store original
        parsed_json=sections       # Store structured
    )
    
    db.add(new_jd)
    db.commit()
    db.refresh(new_jd)
    
    # Extract Skills (Step 4.3)
    from app.services.jd_skill_extractor import extract_jd_skills
    extract_jd_skills(new_jd, db)

    # Extract Experience (Step 4.5)
    from app.services.experience_extractor import extract_experience_requirements
    exp_data = extract_experience_requirements(sections)
    new_jd.min_years_experience = exp_data.get('required_years', 0)
    db.commit() # Save the updates
    
    return {
        "id": new_jd.id,
        "status": "created",
        "sections": list(sections.keys()),
        "min_years_req": new_jd.min_years_experience
    }
