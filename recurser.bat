@echo off
setlocal

set BASE_FILES=-f docker-compose.base.yml
set LOCAL_FILES=%BASE_FILES% -f docker-compose.local.yml
set EXTERNAL_FILES=%BASE_FILES% -f docker-compose.external.yml

if "%1"=="" goto :help
if "%1"=="help" goto :help
if "%1"=="run-local" goto :run-local
if "%1"=="run-external" goto :run-external
if "%1"=="build-local" goto :build-local
if "%1"=="build-external" goto :build-external
if "%1"=="stop" goto :stop
if "%1"=="restart" goto :restart
if "%1"=="status" goto :status
if "%1"=="logs" goto :logs
if "%1"=="remove" goto :remove

echo Unknown command: %1
echo.
goto :help

:run-local
echo Starting services with local LLM...
shift
docker compose %LOCAL_FILES% up %1 %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:run-external
if not exist .env (
    echo Error: .env file not found!
    echo.
    echo To use an external LLM provider:
    echo 1. Copy a template: copy env-templates\openai .env
    echo 2. Edit .env and add your API key
    echo 3. Run this script again
    exit /b 1
)
echo Starting services with external LLM provider...
shift
docker compose %EXTERNAL_FILES% up %1 %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:build-local
echo Building services with local LLM...
shift
docker compose %LOCAL_FILES% build %1 %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:build-external
echo Building services for external LLM provider...
shift
docker compose %EXTERNAL_FILES% build %1 %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:stop
echo Stopping services...
shift
rem Just stop containers, don't remove them
docker compose %LOCAL_FILES% stop %1 %2 %3 %4 %5 %6 %7 %8 %9 2>nul
if errorlevel 1 docker compose %EXTERNAL_FILES% stop %1 %2 %3 %4 %5 %6 %7 %8 %9 2>nul
goto :eof

:restart
echo Restarting services...
shift
rem Restart whichever configuration is currently stopped
docker compose %LOCAL_FILES% restart %1 %2 %3 %4 %5 %6 %7 %8 %9 2>nul
if errorlevel 1 docker compose %EXTERNAL_FILES% restart %1 %2 %3 %4 %5 %6 %7 %8 %9 2>nul
goto :eof

:status
echo Project containers status:
docker compose %LOCAL_FILES% ps 2>nul || docker compose %EXTERNAL_FILES% ps 2>nul || echo No active compose configuration found
goto :eof

:logs
shift
docker compose %LOCAL_FILES% logs -f %1 %2 %3 %4 %5 %6 %7 %8 %9
goto :eof

:remove
echo WARNING: This will remove all containers and volumes for this project!
set /p CONFIRM="Are you sure? (y/N) "
if /i "%CONFIRM%"=="y" (
    echo Detecting project containers...
    
    rem Get current directory name as project name
    for %%I in (.) do set "DIR_NAME=%%~nxI"
    rem Convert to lowercase and replace special chars with hyphen (simplified)
    set "PROJECT_NAME=%DIR_NAME%"
    
    rem Try graceful shutdown with compose
    echo Stopping services...
    docker compose %LOCAL_FILES% down --remove-orphans 2>nul
    set "LLM_API_KEY=dummy"
    set "LLM_API_ENDPOINT=dummy"
    set "LLM_PROVIDER=dummy"
    docker compose %EXTERNAL_FILES% down --remove-orphans 2>nul
    
    rem Remove only containers from this project by label
    echo Removing project containers...
    for /f "tokens=*" %%i in ('docker ps -a -q --filter "label=com.docker.compose.project.working_dir=%CD:\=/%"') do (
        if not "%%i"=="" docker rm -f %%i 2>nul
    )
    
    rem Remove volumes by project name pattern
    echo Removing project volumes...
    docker volume ls -q | findstr /i "%DIR_NAME%" >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%i in ('docker volume ls -q ^| findstr /i "%DIR_NAME%"') do docker volume rm -f %%i 2>nul
    )
    
    echo Project containers and volumes removed
) else (
    echo Cancelled
)
goto :eof

:help
echo Usage: docker.bat [command]
echo.
echo Commands:
echo   run-local      Start services with local LLM
echo   run-external   Start services with external LLM provider
echo   build-local    Build containers for local LLM
echo   build-external Build containers for external LLM
echo   stop           Stop services (containers remain)
echo   restart        Restart stopped services
echo   status         Show status of project containers
echo   logs           Show logs from running services
echo   remove         Remove all project containers and volumes
echo   help           Show this help message
echo.
echo Examples:
echo   docker.bat run-local
echo   docker.bat run-local -d
echo   docker.bat stop
echo   docker.bat restart
echo   docker.bat logs llm-dispatcher
goto :eof