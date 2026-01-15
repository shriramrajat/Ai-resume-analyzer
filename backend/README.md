
# ⚙️ Backend (AI Resume Analyzer)

The core logic engine of the AI Resume Analyzer. Built with FastAPI and PostgreSQL.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL (or SQLite for local demo)

### Setup & Run

1.  **Create Virtual Environment**:
    ```bash
    cd backend
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure Environment**:
    (Optional) Create `.env` file for OpenAI API Key if using live AI features.
    ```
    OPENAI_API_KEY=sk-...
    DATABASE_URL=postgresql://user:pass@localhost/db
    ```

4.  **Run Server**:
    ```bash
    uvicorn main:app --reload
    ```
    API will stay at `http://localhost:8000`.

## 🗄️ Database
- **Models**: `models.py` defines the schema (Resumes, JDs, Skills, Analysis Results).
- **Seeding**: Use `python app/db/seed_db.py` to populate the Skill Ontology.

## 🧠 Key Modules
- **Services**:
    - `pdf_service.py`: PDF text extraction.
    - `parser_rules.py`: Heuristic section detection.
    - `skill_extractor.py`: Ontology-based tagging.
    - `matching_engine.py`: Scorer logic.
    - `llm_service.py`: Generates explanations.
