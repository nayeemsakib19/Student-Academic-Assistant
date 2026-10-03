@echo off
setlocal
cd /d "%~dp0"
if errorlevel 1 (
    echo ERROR: Could not open the project folder.
    pause
    exit /b 1
)

set "VENV=.venv"
set "PYTHON=%VENV%\Scripts\python.exe"

where python >nul 2>nul
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    choice /C YN /N /M "Install Python now using winget? (Y/N): "
    if errorlevel 2 (
        echo Python is required to run this app.
        pause
        exit /b 1
    )

    where winget >nul 2>nul
    if errorlevel 1 (
        echo winget is not available on this PC.
        echo Please install Python manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )

    echo Installing Python via winget...
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    if errorlevel 1 (
        echo ERROR: Python installation failed.
        pause
        exit /b 1
    )

    echo Refreshing PATH for this session...
    set "PATH=%PATH%;%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts"
    where python >nul 2>nul
    if errorlevel 1 (
        echo Python installed, but this terminal cannot find it yet.
        echo Please close and reopen terminal, then run this script again.
        pause
        exit /b 1
    )
)

:: 1. Create venv if it doesn't exist
if not exist "%PYTHON%" (
    echo Creating virtual environment...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo ERROR: Failed to create venv. Make sure Python is installed.
        pause
        exit /b 1
    )
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

:: 2. Install dependencies
echo Installing dependencies...
"%PYTHON%" -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install packages.
    pause
    exit /b 1
)
echo Dependencies installed.

:: 3. Run the app
echo.
echo Starting Smart AI Assistant at http://localhost:8501
echo Press Ctrl+C to stop.
echo.
"%PYTHON%" -m streamlit run app.py

pause
