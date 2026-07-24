@echo off
echo ============================================
echo   VaakShastra Backend - One-Time Setup
echo ============================================
echo.
echo Creating virtual environment...
python -m venv venv
echo.
echo Activating...
call venv\Scripts\activate.bat
echo.
echo Installing packages (wait 1-2 minutes)...
pip install -r requirements.txt
echo.
echo ============================================
echo   SETUP COMPLETE!
echo   Now run: START.bat
echo ============================================
pause
