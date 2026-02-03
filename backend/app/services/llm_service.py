
import json
from typing import List, Dict, Any
from openai import OpenAI, APIError
from app.core.config import settings

# Initialize OpenAI Client
# We intentionally do not throw an error at import time if key is missing,
# but rather fail gracefully during execution or use fallback.
client = None
if settings.OPENAI_API_KEY:
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
else:
    print("WARNING: No OPENAI_API_KEY found. LLM features will return empty results.")

def build_skill_extraction_prompt(section_text: str, allowed_skills: List[str]) -> str:
    """
    Constructs the STRICT SYSTEM PROMPT for AI Skill Extraction.
    """
    allowed_list_str = ", ".join(allowed_skills)
    
    prompt = f"""
    SYSTEM: You are a strict data extraction engine. You are NOT a creative writer.
    
    TASK: Extract technical skills from the provided text using ONLY the Allowed Skills list below.
    
    RULES:
    1. EXTRACT ONLY skills that exactly match names in the Allowed Skills list.
    2. IGNORE any skill not in the list. Do not invent skills. Do not infer skills that are not explicitly supported by evidence.
    3. FOR EACH match, provide the exact quote (evidence) from the text.
    4. OUTPUT MUST be valid JSON list of objects.
    
    ALLOWED SKILLS:
    [{allowed_list_str}]
    
    INPUT TEXT:
    "{section_text}"
    
    OUTPUT FORMAT:
    [
      {{
        "skill": "Exact Name From List",
        "evidence": "Exact quote from text proving usage"
      }}
    ]
    """
    return prompt

def build_jd_skill_extraction_prompt(section_text: str, allowed_skills: List[str]) -> str:
    """
    Constructs the STRICT SYSTEM PROMPT for JD Skill Extraction + Importance.
    """
    allowed_list_str = ", ".join(allowed_skills)
    
    prompt = f"""
    SYSTEM: You are a Job Description Analysis Engine.
    
    TASK: Extract valid technical skills from the text and classify their importance.
    
    RULES:
    1. EXTRACT ONLY skills that exactly match names in the Allowed Skills list.
    2. IGNORE any skill not in the list.
    3. SEARCH for signal phrases to determine importance:
       - CRITICAL: "Must have", "Required", "Key skills", "Proficiency in"
       - OPTIONAL: "Nice to have", "Bonus", "Plus", "Preferred", "Familiarity with"
    4. If unsure, default to CRITICAL if it's in the 'Requirements' section.
    
    ALLOWED SKILLS:
    [{allowed_list_str}]
    
    INPUT TEXT:
    "{section_text}"
    
    OUTPUT FORMAT (Strict JSON List):
    [
      {{
        "skill": "Exact Name From List",
        "importance": "critical" | "optional"
      }}
    ]
    """
    return prompt

def _call_llm_json(prompt: str) -> List[Dict[str, Any]]:
    """
    Helper to call OpenAI with JSON mode forced.
    """
    if not client:
        return []
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        if not content:
            return []
            
        # The prompt asks for a list, but "json_object" mode usually enforces { "key": ... }
        # Sometimes prompts asking for [] at top level break strict json mode or confuse it.
        # We'll parse whatever we get.
        data = json.loads(content)
        
        # If the LLM wrapped it in a key (common behavior even if not asked), extract the list
        if isinstance(data, dict):
             # Look for a list value
             for k, v in data.items():
                 if isinstance(v, list):
                     return v
        if isinstance(data, list):
            return data
            
        return []
        
    except Exception as e:
        print(f"LLM Call Failed: {e}")
        return []

def query_llm_for_skills(section_text: str, allowed_skills: List[str]) -> List[Dict]:
    """
    Extracts skills using LLM.
    """
    prompt = build_skill_extraction_prompt(section_text, allowed_skills)
    # We slightly modify prompt to ensure JSON Object structure for the API
    # But for now, let's rely on the parsing helper
    return _call_llm_json(prompt)

def query_llm_for_jd_skills(section_text: str, allowed_skills: List[str]) -> List[Dict]:
    """
    Extracts JD skills using LLM.
    """
    prompt = build_jd_skill_extraction_prompt(section_text, allowed_skills)
    return _call_llm_json(prompt)

def build_explanation_prompt(analysis_json: Dict) -> str:
    """
    Constructs specific prompt for Phase 6: Explanation Layer.
    """
    json_str = json.dumps(analysis_json, indent=2)
    
    prompt = f"""
    SYSTEM: You are a Career Coach AI. 
    
    TASK: Explain these analysis results without adding new information. You are explaining a precomputed resume-JD analysis. Do not infer, guess, or add new skills. Use only the provided data.
    
    INPUT DATA:
    {json_str}
    
    RULES:
    1. DO NOT RE-CALCULATE ANY SCORES. Trust the input JSON numbers implicitly.
    2. Tone: Professional, Direct, Honest, Constructive.
    3. STRICT OUTPUT FORMAT: You must return a valid JSON object with the following keys:
       - "summary": (String) 1-2 sentences on overall fit.
       - "strengths_explained": (List[String]) Explanation of matched points only.
       - "gaps_explained": (List[String]) Explanation of risks/missing points only.
       - "experience_commentary": (String) Specific comment on years of experience gap/fit.
       - "actionable_recommendations": (List[String]) Specific steps to improve based ONLY on the gaps mentioned.
    4. NO HALLUCINATION. Do not mention skills not in the input.
    """
    return prompt

def generate_ai_explanation(analysis_json: Dict) -> Dict:
    """
    Calls LLM to generate the human-readable explanation.
    """
    if not client:
        # Fallback if AI fails or key missing
        return {
            "summary": "Analysis complete (AI Explanation Unavailable). Please review the detailed checklist below.",
            "strengths_explained": ["AI API Key missing - see raw analysis."],
            "gaps_explained": [],
            "experience_commentary": "Check detailed analysis.",
            "actionable_recommendations": []
        }

    prompt = build_explanation_prompt(analysis_json)
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # 6.5 Validation (Automated Guardrail)
        if validate_ai_response(result):
            return result
        else:
             print("AI Response failed validation")
             
    except Exception as e:
        print(f"Explanation Generation Failed: {e}")
        
    return {
            "summary": "Analysis complete. AI generation failed.",
            "strengths_explained": [],
            "gaps_explained": [],
            "experience_commentary": "",
            "actionable_recommendations": []
        }

def validate_ai_response(response: Dict) -> bool:
    """
    Step 6.5: Validation Rules (Automate These)
    """
    required_keys = ["summary", "strengths_explained", "gaps_explained", "experience_commentary", "actionable_recommendations"]
    
    # 1. Schema Check
    for key in required_keys:
        if key not in response:
            print(f"Validation Failed: Missing key {key}")
            return False
            
    # 2. Type Check
    if not isinstance(response["strengths_explained"], list) or not isinstance(response["gaps_explained"], list):
         print("Validation Failed: Lists are not lists")
         # Attempt to fix if they are strings (some LLMs do bulleted strings)
         return False
         
    return True 
