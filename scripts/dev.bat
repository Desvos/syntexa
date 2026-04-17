@echo off
REM Syntexa Development Launcher for Windows
REM Usage: .\scripts\dev.bat [api|daemon|frontend|all]

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."

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
cd /d "%PROJECT_ROOT%\backend"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
uvicorn syntexa.api.main:app --reload --host 0.0.0.0 --port 8000
goto :eof

:daemon
echo Starting daemon...
cd /d "%PROJECT_ROOT%\backend"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
python -m syntexa.daemon.main
goto :eof

:frontend
echo Starting frontend on http://localhost:5173...
cd /d "%PROJECT_ROOT%\frontend"
bun run dev
goto :eof

:all
echo Starting all services...
echo Note: This will start them sequentially. Use separate terminals for parallel execution.
start "Syntexa API" cmd /k "cd /d %PROJECT_ROOT% && .\scripts\dev.bat api"
timeout /t 2 >nul
start "Syntexa Daemon" cmd /k "cd /d %PROJECT_ROOT% && .\scripts\dev.bat daemon"
timeout /t 2 >nul
start "Syntexa Frontend" cmd /k "cd /d %PROJECT_ROOT% && .\scripts\dev.bat frontend"
echo.
echo All services started in separate windows!
echo API:      http://localhost:8000
echo Frontend: http://localhost:5173
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
