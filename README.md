
# AI Resume Analyzer (Production-Grade)

An engineering-first approach to Resume Analysis that prioritizes determinism, transparency, and explainability over "AI Magic". 

Built with FastAPI, PostgreSQL, and strict logical guardrails.

## 🏗 Architecture

```mermaid
graph TD
    User[Candidate/Recruiter] -->|Upload PDF| API[FastAPI Backend]
    User -->|Paste JD| API
    
    subgraph Ingestion Layer
    API -->|Raw Text| Parser[Heuristic Parser]
    Parser -->|Structured Sections| DB[(PostgreSQL)]
    end
    
    subgraph Async Processing
    API -->|Trigger Analysis| Queue[Background Tasks]
    Queue -->|Fetch Data| Engine[Matching Engine]
    end
    
    subgraph Core Logic
    Engine -->|Extracted Skills| Ontology[Skills Master]
    Engine -->|Compare| Scorer[Weighted Scoring Formula]
    Scorer -->|Facts| Results[Analysis Results]
    end
    
    subgraph Explanation Layer
    Results -->|JSON Facts| AI[LLM (OpenAI)]
    AI -->|Human Text| Explanation[Analysis Explanation]
    end
    
    Explanation -->|Final Report| User
```

The system is designed as a pipeline with strict separation of concerns:

1.  **Ingestion Layer**: 
    - Resumes (PDF) -> `pdfplumber` -> Raw Text -> Normalized Text.
    - JDs (Text) -> Raw Text -> Normalized Text.
2.  **Structural Parsing (Deterministic)**: 
    - Heuristics identify sections (Experience, Skills, Education).
    - **No AI** is used for this structure extraction to ensure reproducibility.
3.  **Knowledge Extraction (Ontology-Bound)**:
    - Skills are extracted *only* if they match the `SkillsMaster` ontology.
    - Confidence is scored based on evidence location (Experience > Skills Section).
    - Experience Years are extracted using Regex (Logic, not LLM).
4.  **Matching Engine (The Heart)**:
    - Inputs: Structured Resume Data + Structured JD Constraints.
    - Output: 0.0 - 1.0 Match Score + Explainable Facts.
    - **Rule**: AI is BANNED from this layer.
5.  **Explanation Layer (The Voice)**:
    - The LLM (OpenAI) acts *only* as a copywriter.
    - It takes the calculated facts and summarizes them.
    - It is explicitly forbidden from re-scoring or hallucinating new data.

## 🧮 Scoring Formula (Explicit)

The score is composed of two parts: **Skill Alignment (70%)** and **Experience Fit (30%)**.

### 1. Skill Score
$$ Score_{skill} = \frac{(Count_{Critical} \times 2.0) + (Count_{Optional} \times 1.0)}{(Total_{Critical} \times 2.0) + (Total_{Optional} \times 1.0)} $$

- **Critical Skills**: Weight 2.0 ("Must Haves")
- **Optional Skills**: Weight 1.0 ("Nice to Haves")
- **Threshold**: A skill is only "Matched" if confidence > 0.6 (Mentioning != Knowing).

### 2. Experience Score
Derived from `Gap = Actual Years - Required Years`.

- **Gap >= 0**: Score 1.0 (Perfect Fit)
- **Gap = -1**: Score 0.8 (Minor Penalty)
- **Gap < -1**: Score 0.5 (Severe Penalty)

### 3. Final Calculation
$$ FinalScore = (Score_{skill} \times 0.70) + (Score_{experience} \times 0.30) $$

## 🤖 AI Usage Boundaries

| Feature | Logic | AI Role |
| :--- | :--- | :--- |
| **Parsing** | Regex + Rules | ❌ None |
| **Skill Extraction** | Ontology Lookup | ❌ None (Heuristic Fallback) / ✅ Hybrid valid |
| **Scoring** | Weighted Math | ❌ BANNED |
| **Explanation** | N/A | ✅ Copywriting Only |

## ⚠️ Known Limitations

1.  **Ontology Dependence**: If a skill is not in `skills_master`, it is ignored. This avoids hallucinations but requires database maintenance.
2.  **Formatting Sensitivity**: While `pdfplumber` is robust, extremely creative layouts (2-column non-standard) may degrade section detection.
3.  **Language Support**: English only.

## ⚖️ Ethical Considerations

- **Bias Reduction**: The system ignores names, genders, and colleges during scoring. It looks ONLY at Skills and Experience Years.
- **Explainability**: Every rejection can be traced to a specific missing skill or experience gap. "Black Box" rejection is impossible by design.