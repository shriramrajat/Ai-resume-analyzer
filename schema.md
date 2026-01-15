# 🔒 LOCKED DATA SCHEMA

> **STATUS**: FROZEN
> **LAST UPDATED**: 2026-01-15
> **NOTE**: This document is the SINGLE SOURCE OF TRUTH. Do not deviate from this structure in code or AI prompts.

---

## 1. CORE PRINCIPLES
1.  **Deterministic Storage**: If it cannot be stored in a database column or a defined JSON shape, it does not exist.
2.  **Raw Data Preservation**: We always store the raw input (text) to allow re-parsing/re-analysis.
3.  **Strict Typing**: Confidence is a float. Categories are Enums. Existence is boolean.

---

## 2. DATABASE SCHEMA (PostgreSQL)

### Table 1: `resumes`
*Stores the raw and initial processed state of uploaded resumes.*

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Integer | PK | Unique identifier for the resume. |
| `user_id` | String/UUID | Not Null | Owner of the resume. |
| `file_path` | String | Not Null | Path to the stored PDF file (local/S3). |
| `raw_text` | Text | Not Null | **Source of Truth**. Extracted text content. |
| `created_at` | Timestamp | Default Now | Upload timestamp. |

**Rationale**: `raw_text` allows us to improve parsing logic later without asking the user to re-upload.

### Table 2: `job_descriptions`
*Stores job descriptions against which resumes are compared.*

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Integer | PK | Unique identifier for the JD. |
| `raw_text` | Text | Not Null | The job description text. |
| `created_at` | Timestamp | Default Now | Creation timestamp. |

**Rationale**: Keep it minimal. JDs are static references.

### Table 3: `skills_master` (CRITICAL)
* The controlled vocabulary of skills. No free-text skills allowed in analysis.*

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Integer | PK | Unique identifier. |
| `name` | String | Unique, Not Null | Normalized skill name (e.g., "Python"). |
| `category` | String/Enum | Not Null | Type: `language`, `framework`, `tool`, `concept`. |

**Rationale**: Prevents "Python 3" vs "python" duplicates. Without this, matching is impossible.

### Table 4: `resume_skills`
*Skills found in a specific resume, with evidence.*

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Integer | PK | Unique identifier. |
| `resume_id` | FK | `resumes.id` | Link to resume. |
| `skill_id` | FK | `skills_master.id` | Link to canonical skill. |
| `confidence_score` | Float | 0.0 - 1.0 | Rule-based confidence (not LLM felt-cute score). |
| `evidence_text` | Text | Nullable | Snippet where skill was found. |

**Rationale**: Traceability. usage of "Python: yes" is banned.

### Table 5: `jd_skills`
*Skills required by a specific Job Description.*

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Integer | PK | Unique identifier. |
| `jd_id` | FK | `job_descriptions.id` | Link to JD. |
| `skill_id` | FK | `skills_master.id` | Link to canonical skill. |
| `importance` | Enum | `critical`, `optional` | Weighting factor for matching. |

**Rationale**: Not all requirements are equal.

### Table 6: `analysis_results`
*Snapshots of analysis runs.*

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID/Integer | PK | Unique identifier. |
| `resume_id` | FK | `resumes.id` | Snapshot target (Resume). |
| `jd_id` | FK | `job_descriptions.id` | Snapshot target (JD). |
| `overall_match_score`| Float | | Final computed score. |
| `result_json` | JSONB | Not Null | The full structured output (see Section 3). |
| `created_at` | Timestamp | Default Now | When analysis ran. |

**Rationale**: Reproducibility. Never recompute silently.

---

## 3. OUTPUT JSON SCHEMA
*The only format the Analysis Engine is allowed to produce.*

```json
{
  "overall_match_score": 0.0,
  "skill_analysis": {
    "matched": [
      { "skill": "Python", "confidence": 0.9, "importance": "critical" }
    ],
    "missing_critical": [
      { "skill": "FastAPI", "importance": "critical" }
    ],
    "missing_optional": []
  },
  "experience_analysis": {
    "required_years": 0, /* Parsed from JD */
    "actual_years": 0,   /* Computed from Resume */
    "gap": 0             /* required - actual */
  },
  "strengths": [
    "Strong Python evidence across 3 roles"
  ],
  "risks": [
    "Short tenure in last role (6 months)"
  ],
  "recommendations": [
    "Highlight API design experience more clearly"
  ]
}
```

**Rationale**: 
1. `experience_analysis` is math, not opinion.
2. `strengths`/`risks` are the only place for "LLM reasoning".
3. `skill_analysis` is derived strictly from DB relations.
