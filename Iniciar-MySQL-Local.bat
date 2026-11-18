@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto venv
if exist "venv\Scripts\python.exe" goto venv_alternativa
where py >nul 2>&1
if errorlevel 1 (
    python -m scripts.iniciar_mysql_local %*
) else (
    py -3 -m scripts.iniciar_mysql_local %*
)
goto fim
:venv
".venv\Scripts\python.exe" -m scripts.iniciar_mysql_local %*
goto fim
:venv_alternativa
"venv\Scripts\python.exe" -m scripts.iniciar_mysql_local %*
:fim
pause
