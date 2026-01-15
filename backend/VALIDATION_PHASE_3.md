
# 3.6 Validation Checklist Verification

## 1. Can I list all supported skills?
YES. 
- Source: `skills_master` table.
- Seed file: `backend/data/skills_master_seed.json`.
- Status: I just ran the seeding script to ensure they are in the DB.

## 2. Can I explain why a skill was extracted?
YES.
- Logic: `backend/app/services/skill_extractor.py`.
- Explanation: The code explicitly looks for substrings in specific sections (`Experience` vs `Skills` list) which determines the confidence score.

## 3. Can I show evidence for every skill?
YES.
- Storage: `resume_skills` table has an `evidence_text` column.
- Logic: The extractor saves a snippet (`...text content...`) surrounding the match.

## 4. Can two runs give identical output?
YES.
- Mechanism: The extractor is primarily rule-based and deterministic.
- Idempotency: The extraction function deletes previous skills for the resume_id before inserting new ones, ensuring clean re-runs.
- Persistence: Once stored in DB, we read from DB, not re-parse.

## SYSTEM STATUS
- **Tables**: Created.
- **Seeds**: Loaded (Python, FastAPI, Docker, etc.).
- **Pipeline**: Upload -> Parse -> Extract -> Save.

READY FOR PHASE 4.
