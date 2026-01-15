
import pdfplumber

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts raw text from a PDF file using pdfplumber.
    
    Why pdfplumber? 
    It offers better layout preservation than standard PyPDF2.
    We are intentionally NOT using OCR (Tesseract) yet, because:
    1. It's slow.
    2. Most digital resumes are text-selectable.
    3. OCR introduces noise that confuses our keyword matchers.
    """
    text_content = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            # We iterate page by page to handle multi-page resumes correctly
            for page in pdf.pages:
                # extract_text(x_tolerance=1, y_tolerance=1) helps closely grouped text stay together
                # keeping it simple: default extract_text
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
                    
        raw_text = "\n".join(text_content)
        
        # Apply strict normalization (Step 2.3)
        from app.core.text_utils import normalize_text
        return normalize_text(raw_text)
    except Exception as e:
        # Re-raise with clear context
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
