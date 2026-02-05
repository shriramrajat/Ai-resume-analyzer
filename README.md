
<div align="center">

# 📄 AI Resume Analyzer
### *Precision Recruiting with Deterministic Logic & AI Explainability*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-key-features">Key Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-api-documentation">API Docs</a>
</p>

</div>

---

## 🔭 Overview

**AI Resume Analyzer** is an engineering-first solution to the recruitment problem. Unlike black-box AI tools that "guess" a candidate's fit, this system prioritizes **determinism, transparency, and logical guardrails**.

It uses a hybrid approach:
1.  **Deterministic Logic** for parsing and scoring to ensure fairness and reproducibility.
2.  **Generative AI (LLMs)** *only* for natural language summarization and explanation.

This ensures that every rejection can be traced to a specific missing skill or experience gap, making the "why" transparent to both recruiters and candidates.

## ✨ Key Features

- **🛡️ Deterministic Parsing**: Standardizes resume structure using heuristic rules, not AI guesses.
- **🧠 Ontology-Bound Extraction**: Skills are extracted and validated against a strictly defined `SkillsMaster` ontology.
- **⚖️ Transparent Scoring**: 
    - **Skill Match (70%)**: Weighted scoring based on "Must-Have" vs "Nice-to-Have" skills.
    - **Experience Fit (30%)**: Calculated based on logic-driven experience gaps.
- **🚫 Anti-Hallucination**: The scoring engine is mathematically pure and explicitly forbids AI from making decisions.
- **🗣️ Explainable AI**: OpenAI's GPT is used solely as a copywriter to explain the *mathematical* results in human-readable definitions.
- **⚡ Real-time Analysis**: Fast feedback loop for immediate insights.

## 🏗 Architecture

The system follows a strict pipeline separation to significantly reduce the risk of AI hallucination.

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
    Results -->|JSON Facts| AI["LLM (OpenAI)"]
    AI -->|Human Text| Explanation[Analysis Explanation]
    end
    
    Explanation -->|Final Report| User
```

### 🧠 Decision Logic
| Feature | Implementation | AI Role |
| :--- | :--- | :--- |
| **Parsing** | Regex + Heuristics | ❌ None |
| **Skill Extraction** | Ontology DB Lookup | ❌ None (Heuristic Fallback) |
| **Scoring** | Weighted Math Formula | ❌ BANNED |
| **Explanation** | Prompt Engineering | ✅ Copywriting Only |

## 🛠 Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **PDF Processing**: `pdfplumber`
- **AI Integration**: OpenAI API (GPT-4o/GPT-3.5)
- **Validation**: Pydantic / `pydantic-settings`
- **Testing**: Pytest

### Frontend
- **Framework**: React (Vite)
- **Language**: TypeScript
- **Styling**: Vanilla CSS / CSS Modules
- **State**: React Hooks

## 🚀 Getting Started

Follow these instructions to set up the project locally.

### Prerequisites
- Python 3.10+
- Node.js & npm
- PostgreSQL (Running locally or via Docker)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/shriramrajat/Ai-Resume-Analyzer.git
cd Ai-Resume-Analyzer
```

### 2️⃣ Backend Setup
Navigate to the backend directory and set up the Python environment.

```bash
cd backend
python -m venv venv
# Windows
.\venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

**Environment Variables**:
Create a `.env` file in the `backend` directory:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/resume_db
OPENAI_API_KEY=your_openai_api_key
```

**Database Init**:
```bash
# Initialize DB tables (Assuming you have a script or running app does it)
python main.py
```

### 3️⃣ Frontend Setup
Open a new terminal and navigate to the frontend directory.

```bash
cd frontend
npm install
npm run dev
```

The UI should now be accessible at `http://localhost:5173`.

## 📖 API Documentation

The backend provides auto-generated Swagger UI documentation.
1. Start the backend: `uvicorn main:app --reload`
2. Visit: `http://localhost:8000/docs`

## 🧮 Scoring Formula Details

The score is calculated via a strictly defined formula:

$$ FinalScore = (Score_{skill} \times 0.70) + (Score_{experience} \times 0.30) $$

- **Skill Score**: Ratio of matched critical (2.0x) and optional (1.0x) skills.
- **Experience Score**: Penalty-based function on `Actual Years - Required Years`.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements.