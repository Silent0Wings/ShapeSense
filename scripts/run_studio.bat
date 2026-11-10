@echo off
rem Starts ShapeSense Studio from the repository's virtual environment.
cd /d "%~dp0.."
call .venv\Scripts\activate.bat
rem Opens the dashboard once the server answers.
start "" /b cmd /q /c "for /l %%i in (1,1,60) do (curl -s -o nul http://localhost:8765/ && (start http://localhost:8765 & exit) || ping -n 2 127.0.0.1 >nul)"
python -m studio
pause
