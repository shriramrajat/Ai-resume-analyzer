@echo off
echo ===================================================
echo   AI Resume Analyzer - Dev Validation Launcher
echo ===================================================

echo 1. Launching Backend (FastAPI)...
start "Backend API (Port 8000)" cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload"

echo 2. Launching Frontend (Vite)...
start "Frontend UI (Port 5173)" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo   System Starting...
echo   1. Backend: http://localhost:8000/docs
echo   2. Frontend: http://localhost:5173
echo.
echo   NOTE: Ensure your Database is running!
echo ===================================================
pause
