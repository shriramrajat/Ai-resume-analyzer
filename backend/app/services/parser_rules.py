
import re
from typing import Dict, List, Tuple

# Mapping of standardized section names to possible header keywords
# All keywords MUST be lowercase because input text is pre-normalized
SECTION_HEADERS_MAPPING = {
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "internships"
    ],
    "skills": [
        "skills",
        "technical skills",
        "core competencies",
        "technologies",
        "tech stack",
        "skills & expertise"
    ],
    "education": [
        "education",
        "academic background",
        "qualifications",
        "certifications",
        "scholastic achievements"
    ],
    "projects": [
        "projects",
        "personal projects",
        "academic projects",
        "key projects"
    ]
}

def detect_sections(normalized_text: str) -> Dict[str, str]:
    """
    Splits the normalized text into sections based on heuristic headers.
    
    Strategy:
    1. Identify lines that look like headers (short, keywords matching mapping).
    2. Record start indices of these sections.
    3. Slice text between start of one section and start of next.
    4. Store in dict.
    
    Returns:
        Dict with keys 'experience', 'skills', 'education', 'projects' 
        and values as the captured text block.
    """
    lines = normalized_text.split('\n')
    sections = {
        "experience": [],
        "skills": [],
        "education": [],
        "projects": [],
        "uncategorized": [] # Capture header/summary info
    }
    
    current_section = "uncategorized"
    
    # Heuristics for Header Detection:
    # We are looking for lines that are clearly NOT content.
    # 1. Line is short (< 50 chars) -> Content sentences are usually longer.
    # 2. Line matches a keyword in SECTION_HEADERS_MAPPING
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        # Check if this line is a header
        is_header = False
        new_section_type = None
        
        # Only check short lines. If a line is long, it's likely a description, 
        # even if it accidentally contains the word "experience".
        if len(line_clean) < 50: 
            for section_type, keywords in SECTION_HEADERS_MAPPING.items():
                # We developed a specific regex to catch "Skills:" or "Work Experience"
                # while avoiding embedded usage like "I gained experience in..."
                for kw in keywords:
                    # Regex anchor ^ ensures we only match start of line.
                    pattern = f"^{kw}[:\s-]*$"
                    if re.match(pattern, line_clean):
                        is_header = True
                        new_section_type = section_type
                        break
                if is_header:
                    break
        
        if is_header:
            current_section = new_section_type
            # We DONT add the header line itself to the content? 
            # Usually better to exclude it to keep "skills" clean.
            continue
            
        # Add line to current section
        sections[current_section].append(line)
        
    
    # Join lists back to text blobs
    result = {k: "\n".join(v).strip() for k, v in sections.items()}
    return result

# JD Specific Headers
JD_HEADERS_MAPPING = {
    "responsibilities": [
        "responsibilities",
        "what you will do",
        "what you'll do",
        "duties",
        "role overview",
        "key responsibilities"
    ],
    "requirements": [
        "requirements",
        "what we work with",
        "what we are looking for",
        "minimum qualifications",
        "basic qualifications",
        "what you need",
        "skills required",
        "tech stack"
    ],
    "nice_to_have": [
        "nice to have",
        "preferred qualifications",
        "bonus points",
        "plus",
        "what makes you stand out"
    ]
}

def detect_jd_sections(normalized_text: str) -> Dict[str, str]:
    """
    Parses Job Descriptions into structured buckets.
    Similar logic to detect_sections but uses JD_HEADERS_MAPPING.
    """
    lines = normalized_text.split('\n')
    sections = {
        "responsibilities": [],
        "requirements": [],
        "nice_to_have": [],
        "uncategorized": [] 
    }
    
    current_section = "uncategorized"
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        is_header = False
        new_section_type = None
        
        # JDs often have longer headers like "What you will trigger" so we relax the length check slightly
        if len(line_clean) < 80:
            for section_type, keywords in JD_HEADERS_MAPPING.items():
                for kw in keywords:
                    # Case insensitive match already handled by lowercase input?
                    # Yes, input is normalized.
                    # Keyword must be at start of line
                    pattern = f"^{kw}[:\s-]*$"
                    if re.match(pattern, line_clean):
                        is_header = True
                        new_section_type = section_type
                        break
                if is_header:
                    break
        
        if is_header:
            current_section = new_section_type
            continue
            
        sections[current_section].append(line)
        
    return {k: "\n".join(v).strip() for k, v in sections.items()}
