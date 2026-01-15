
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Resume
import shutil
import os
import uuid

router = APIRouter()

UPLOAD_DIR = "uploads/resumes"

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...), 
    user_id: str = "default_user", # Placeholder until Auth is implemented
    db: Session = Depends(get_db)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    # Create unique filename to prevent overwrites
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file content
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save file: {str(e)}")
    
    # Extract raw text (Step 2.2)
    # We do this immediately after upload to ensure raw_text is populated
    from app.services.pdf_service import extract_text_from_pdf
    
    try:
        raw_text = extract_text_from_pdf(file_path)
    except Exception as e:
        # If extraction fails, we should probably fail the upload or store error state.
        # For now, failing the upload is safer than storing a corrupt state.
        os.remove(file_path) # Cleanup
        raise HTTPException(status_code=400, detail=f"PDF Parsing Failed: {str(e)}")

    # Detect Sections (Step 2.4)
    from app.services.parser_rules import detect_sections
    sections = detect_sections(raw_text)

    # Create DB Entry
    new_resume = Resume(
        user_id=user_id,
        file_path=file_path,
        raw_text=raw_text,
        parsed_json=sections,
        is_parsed=True
    )
    
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    
    # Extract Skills (Step 3.5)
    # We populate resume_skills immediately.
    # This prevents re-computation later.
    from app.services.skill_extractor import extract_skills_hybrid
    
    # Note: We can add a try/except here if we want to isolate skill extraction failures 
    # from the upload success, but for now we treat it as part of the pipeline.
    extracted_skills = extract_skills_hybrid(new_resume, db)
    
    return {
        "id": new_resume.id,
        "filename": unique_filename,
        "status": "uploaded_and_processed",
        "sections_found": list(sections.keys()),
        "skills_found_count": len(extracted_skills)
    }
