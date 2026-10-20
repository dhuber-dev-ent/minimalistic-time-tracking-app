@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

set "LOCKFILE=%~dp0data\.last_run"
set "TODAY=%date:~-4%%date:~-7,2%%date:~-10,2%"

if exist "%LOCKFILE%" (
    set /p LAST_RUN=<"%LOCKFILE%"
    if "!LAST_RUN!"=="%TODAY%" (
        echo Already started today.
        timeout /t 3 >nul
        exit /b
    )
)

echo %TODAY%>"%LOCKFILE%"
"C:\Users\HUD2FH\.conda\envs\analysis\python.exe" start.py
