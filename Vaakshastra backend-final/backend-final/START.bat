@echo off
echo ============================================
echo   VaakShastra Backend - Starting Server
echo ============================================
echo.
echo   Website:  http://localhost:8000/site
echo   API Docs: http://localhost:8000/docs
echo   Press Ctrl+C to stop
echo.
echo ============================================
call venv\Scripts\activate.bat
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
