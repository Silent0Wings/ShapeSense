@echo off
rem Starts ShapeSense Studio from the repository's virtual environment.
cd /d "%~dp0.."
call .venv\Scripts\activate.bat
python -m studio
pause
