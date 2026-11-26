@echo off
rem Direct LLM classification: Claude (claude CLI) and Gemini (agy CLI) each fill in an unlabelled predictions CSV
rem for the same 200 blind test images, then the script scores macro F1 against the trained CNN.
rem Usage: scripts\llm_classify.bat [--models claude,gemini] [--batches 1,2] [--dry-run]
rem Needs both CLIs installed and signed in. Details: scripts\llm_classify.py
setlocal
cd /d "%~dp0.."
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m scripts.llm_classify %*
) else (
    python -m scripts.llm_classify %*
)
exit /b %errorlevel%
