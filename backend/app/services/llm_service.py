
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
