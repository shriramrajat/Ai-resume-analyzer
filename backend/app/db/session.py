
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL should be in environment variables in production
# For now, using sqlite for local development as previously implied, 
# although User requested PostgreSQL. I will set up the structure for PostgreSQL.
# User Requirement: DB: PostgreSQL
# I will assume a standard connection string for now, but will likely need a 
# docker-compose or local setup later.
# For this step, I will use a placeholder or local sqlite if postgres is not ready,
# but strictly following the request: "Language: Python... Framework: FastAPI... DB: PostgreSQL"

# Database URL provided by User
# Requirement: DB: PostgreSQL
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:NewStrongPassword123@localhost:5432/AIResumeAnalyser"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
