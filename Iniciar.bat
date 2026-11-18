@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
    python -m scripts.iniciar %*
) else (
    py -3 -m scripts.iniciar %*
)
pause
