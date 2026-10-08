@echo off
REM ============================================================================
REM FIR Audio Verification System - Windows Batch Launcher
REM ============================================================================

cd /d "%~dp0"
echo Starting FIR Audio Verification System...
.venv\Scripts\python.exe python\main.py %*
pause
