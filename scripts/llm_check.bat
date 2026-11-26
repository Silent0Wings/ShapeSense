@echo off
rem Dataset-awareness check: send the same prompt to Claude (claude CLI) and Gemini (agy CLI), save both replies.
rem Usage: scripts\llm_check.bat [--models claude,gemini] [--dry-run]
rem Needs both CLIs installed and signed in. Details: scripts\llm_check.py
setlocal
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m scripts.llm_check %*
) else (
    python -m scripts.llm_check %*
)
exit /b %errorlevel%
