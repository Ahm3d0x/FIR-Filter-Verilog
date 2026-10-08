@echo off
REM ============================================================================
REM FIR Audio Test Tool - Root Launcher
REM ============================================================================

cd /d "%~dp0"
echo Starting FIR Audio Test Tool GUI...
".venv\Scripts\python.exe" Audio_Test_Tool\src\gui_app.py
if %ERRORLEVEL% NEQ 0 pause
