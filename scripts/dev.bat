ccd
@echo off
REM Syntexa Development Launcher for Windows
REM Usage: .\scripts\dev.bat [api|daemon|frontend|all]

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "BACKEND_DIR=%PROJECT_ROOT%\backend"

echo Syntexa Development Launcher

if "%~1"=="" goto :help
if /I "%~1"=="api" goto :api
if /I "%~1"=="daemon" goto :daemon
if /I "%~1"=="frontend" goto :frontend
if /I "%~1"=="all" goto :all
if /I "%~1"=="help" goto :help
if /I "%~1"=="--help" goto :help
if /I "%~1"=="-h" goto :help

echo Unknown command: %~1
goto :help

:api
echo Starting API server on http://localhost:8000...
cd /d "%BACKEND_DIR%"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python -m uvicorn syntexa.api.main:app --reload --host 0.0.0.0 --port 8000
) else (
    python -m uvicorn syntexa.api.main:app --reload --host 0.0.0.0 --port 8000
)
goto :eof

:daemon
echo Starting daemon...
cd /d "%BACKEND_DIR%"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    python -m syntexa.daemon.main
) else (
    python -m syntexa.daemon.main
)
goto :eof

:frontend
echo Starting frontend on http://localhost:5173...
cd /d "%PROJECT_ROOT%\frontend"
bun run dev
goto :eof

:all
echo Starting all services...
echo Opening separate windows for each service...
start "Syntexa API" cmd /k "cd /d "%BACKEND_DIR%" & (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat) & python -m uvicorn syntexa.api.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 >nul
start "Syntexa Daemon" cmd /k "cd /d "%BACKEND_DIR%" & (if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat) & python -m syntexa.daemon.main"
timeout /t 2 >nul
start "Syntexa Frontend" cmd /k "cd /d "%PROJECT_ROOT%\frontend" & bun run dev"
echo.
echo All services started in separate windows!
echo API:      http://localhost:8000
echo Frontend: http://localhost:5173
echo.
echo Close each window to stop the service.
goto :eof

:help
echo.
echo Usage: .\scripts\dev.bat [COMMAND]
echo.echo Commands:
echo   api       - Start API server with auto-reload (port 8000)
echo   daemon    - Start daemon
echo   frontend  - Start frontend dev server (port 5173)
echo   all       - Start all services in separate windows
echo   help      - Show this help
echo.echo Examples:
echo   .\scripts\dev.bat api       - API only
echo   .\scripts\dev.bat frontend - Frontend only
echo   .\scripts\dev.bat all       - Full stack
echo.
