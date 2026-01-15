
from fastapi import FastAPI
from app.api.v1 import resume
from app.db.session import engine
from app.db.models import Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Resume Analyzer")

app.include_router(resume.router, prefix="/api/v1/resume", tags=["resume"])

from app.api.v1 import jd
app.include_router(jd.router, prefix="/api/v1/jd", tags=["jd"])

@app.get("/")
def read_root():
    return {"message": "System Operational"}
