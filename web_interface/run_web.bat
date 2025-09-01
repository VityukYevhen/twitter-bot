@echo off
echo ==============================
echo  Twitter Bot Web Interface
echo ==============================
cd /d "%~dp0"

echo Creating/activating virtual environment...
if not exist ..\venv (
  py -m venv ..\venv
)
call ..\venv\Scripts\activate.bat

echo Installing requirements...
py -m pip install --upgrade pip >nul 2>&1
py -m pip install -r requirements_web.txt

echo Starting server...
py app.py

pause
