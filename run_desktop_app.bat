@echo off
REM ============================================================================
REM  Python Speech-to-Text Desktop Application Launcher
REM  Starts the Python GUI desktop app
REM ============================================================================

echo.
echo ========================================
echo  Python STT Desktop App
echo ========================================
echo.
echo Starting Python GUI...
echo.

cd /d "%~dp0"

REM Activate local virtual environment if available
if exist ".venv\Scripts\Activate.ps1" (
    powershell -ExecutionPolicy Bypass -NoProfile -Command "& '.\.venv\Scripts\Activate.ps1'; python main.py"
) else (
    python main.py
)

