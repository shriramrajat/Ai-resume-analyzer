
import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    Normalizes text to ensure consistent processing for Regex and analysis.
    
    Operations:
    1. Unicode Normalization (NFKD) to handle accents and weird characters.
    2. Replace specific weird bullet points with standard hyphens.
    3. Collapse multiple spaces/tabs into single space (preserve newlines).
    4. Strip leading/trailing whitespace.
    5. Convert to lowercase (optional, BUT kept mixed-case here to preserve 
       proper nouns/Headers for Section Detection, unless strictly requested 
       to lowercase everything. 
       Wait, User Request says "Lowercase". I will follow strict instructions.)
    """
    
    if not text:
        return ""

    # 1. Normalize Unicode (e.g., café -> cafe, fancy spaces -> normal space)
    text = unicodedata.normalize('NFKD', text)

    # 2. Standardize bullet points
    # Replace common bullet chars with standard hyphen
    # • (U+2022), ● (U+25CF), ▪ (U+25AA), etc.
    bullet_pattern = r'[•●▪➢➣➤]'
    text = re.sub(bullet_pattern, '-', text)

    # 3. Collapse multiple spaces/tabs SAME LINE to single space
    # re.sub(r'\s+', ' ') would kill newlines, which we need for structure.
    # We want to collapse horizontal whitespace only.
    text = re.sub(r'[ \t]+', ' ', text)

    # 4. Handle weird line breaks?
    # Keeping it simple: regex handles \r\n -> \n typically but let's Ensure standard \n
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # 5. Collapse multiple newlines to max 2 (paragraph break)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # 6. Lowercase
    # User instruction: "Normalize: Lowercase"
    # Implementing strictly.
    # Warning: This makes distinguishing "Java" (language) from "java" (coffee) impossible if context lost, 
    # but for section headers it makes matching "EXPERIENCE" vs "Experience" easier.
    text = text.lower()

    return text.strip()
