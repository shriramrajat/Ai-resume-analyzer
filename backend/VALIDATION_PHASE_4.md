
# 4.7 Validation Checklist Verification

## 1. JD processing works without a resume?
YES. 
- Endpoint: `POST /jd/create` depends only on JD text. 
- It has zero imports from the Resume module.

## 2. Skills come only from ontology?
YES.
- Logic: `jd_skill_extractor.py` queries `SkillsMaster` table and builds a hashmap `skill_map = {s.name.lower(): s for s in all_skills}`.
- Enforcement: It only iterates keys in this map. Unknown words are ignored.

## 3. Critical vs optional is explainable?
YES.
- Default: `Requirements` section -> Critical. `Nice-to-have` -> Optional.
- Overrides: `determine_importance` function explicitly checks keywords:
  - "Must", "Required" -> Critical
  - "Bonus", "Plus" -> Optional
- This logic is hard-coded and inspectable (not black-box).

## 4. Experience requirements are numeric, not vibes?
YES.
- Logic: `experience_extractor.py`.
- Regex: `r'(\d+)(?:\+?|\s*(?:-|\s+to\s+)\s*\d+)?\s*years?'`
- Type: Stored as `Integer` in `min_years_experience` column.

## SYSTEM STATUS
- **Resumes**: Upload -> Text -> Sections -> DB.
- **JDs**: Create -> Text -> Sections -> Skills(Ontology) + Exp(Numeric) -> DB.
- **Next**: Matching Engine.

READY FOR PHASE 5.
