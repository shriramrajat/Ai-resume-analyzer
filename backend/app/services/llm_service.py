
import json
from typing import List, Dict
# Placeholder for OpenAI/LLM client - strictly used as a logic engine, not a knowledge base.
# In a real scenario, this would import openai or langchain.
# For now, I'll simulate the interface or use a dummy implementation if no API key is provided.
# User Requirements: "LLM: OpenAI / Claude (ONLY for reasoning & explanation)"

# Since I don't have the User's API Key, I will write the PROMPT TEXT and the structure
# to call the LLM, but I might need to mock the response or ask for a key.
# I will implement the *functions* assuming the client exists.

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

# Dummy LLM wrapper for now - intended to be replaced with actual OpenAI call
# I will create a place to put the API key later.
def query_llm_for_skills(section_text: str, allowed_skills: List[str]) -> List[Dict]:
    """
    Simulates sending the prompt to an LLM and getting strictly formatted JSON back.
    This function isolates the "AI Danger Zone".
    """
    prompt = build_skill_extraction_prompt(section_text, allowed_skills)
    
    # TODO: Connect to OpenAI API here.
    # For the purpose of this "Build Phase", I will define the contract.
    # If the user provides an API Key in .env, this would work.
    
    # Mock response for testing the pipeline if called without key
    return [] 

def query_llm_for_jd_skills(section_text: str, allowed_skills: List[str]) -> List[Dict]:
    """
    Simulates JD extraction LLM call.
    """
    prompt = build_jd_skill_extraction_prompt(section_text, allowed_skills)
    return [] 

def build_explanation_prompt(analysis_json: Dict) -> str:
    """
    Constructs specific prompt for Phase 6: Explanation Layer.
    Feeding ONLY the structured analysis result.
    """
    import json
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
    Returns: Dict matching the strict schema.
    """
    prompt = build_explanation_prompt(analysis_json)
    
    # Mock Response for Validation
    response = {
        "summary": "Your profile shows potential but lacks key technical requirements.",
        "strengths_explained": [
            "Strong foundation in Python is evident.",
            "Backend experience aligns with general domain."
        ],
        "gaps_explained": [
            "Critically missing Docker, which is a required hard skill.",
            "Experience is 1 year short of the minimum requirement."
        ],
        "experience_commentary": "The role requires 3 years, but you have 2. This gap triggers a penalty score.",
        "actionable_recommendations": [
            "Build a small project using Docker/Kubernetes.",
            "Highlight any freelance or side projects to bridge the experience gap."
        ]
    }
    
    # 6.5 Validation (Automated Guardrail)
    if not validate_ai_response(response):
        # Fallback if AI fails validation
        return {
            "summary": "Analysis complete. Please review the detailed checklist below.",
            "strengths_explained": [],
            "gaps_explained": [],
            "experience_commentary": "Check detailed analysis.",
            "actionable_recommendations": []
        }
        
    return response

def validate_ai_response(response: Dict) -> bool:
    """
    Step 6.5: Validation Rules (Automate These)
    1. Check JSON Schema (Keys must exist)
    2. (Constraint) Ensure no extra/hallucinated skills? 
       - Hard to regex every word, but we ensure structure is correct.
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
         return False
         
    return True 
