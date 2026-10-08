@echo off
REM ============================================================================
REM Audio Test Tool Launcher
REM ============================================================================

cd /d "%~dp0.."
".venv\Scripts\python.exe" Audio_Test_Tool\src\gui_app.py
if %ERRORLEVEL% NEQ 0 pause
