
import re
from typing import Optional, Dict

def extract_years_of_experience(text_lower: str) -> Optional[int]:
    """
    Extracts explicit years of experience requirements using regex.
    Returns the maximum year requirement found (conservative estimate for 'Senior' roles, 
    but for filtering usually min is better? 
    Prompt says: '3+ years' -> 3. So we extract the number.
    If multiple found (e.g. 5+ Python, 2+ Cloud), logic gets complex.
    We'll return the MAX found in the 'Requirements' section as a general heuristic 
    for the ROLE's seniority.
    """
    # Patterns: 
    # "3+ years"
    # "3-5 years"
    # "at least 3 years"
    # "minimum of 3 years"
    
    # \d+ matches number
    # \s* matches optional space
    # (?:-|\s+to\s+)?\s*\d* handles range like "3-5" or "3 to 5" (we take the first number)
    # years? matches year or years
    
    pattern = r'(\d+)(?:\+?|\s*(?:-|\s+to\s+)\s*\d+)?\s*years?'
    
    matches = re.finditer(pattern, text_lower)
    
    years_found = []
    for m in matches:
        val = int(m.group(1))
        # Sanity check: unlikely to ask for 200 years. unlikely to be 1990 years (date).
        if 0 < val < 20: 
            years_found.append(val)
            
    if not years_found:
        return 0
        
    # Heuristic: The highest number usually defines the Seniority Level of the listing.
    return max(years_found)

def extract_experience_requirements(sections: Dict[str, str]) -> Dict:
    """
    Parses sections to find explicit experience requirements.
    """
    # Focus mainly on 'requirements' or 'responsibilities'
    # Prioritize Requirements
    
    text_blob = sections.get('requirements', '') + " " + sections.get('uncategorized', '')
    text_blob = text_blob.lower()
    
    required_years = extract_years_of_experience(text_blob)
    
    return {
        "required_years": required_years
    }
