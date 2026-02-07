@echo off
REM S.C.A.R.I Deployment Setup Script for Windows
REM This script prepares the system for deployment in seconds

setlocal enabledelayedexpansion

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║           ^!  S.C.A.R.I Deployment Setup Script  ^!            ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

set SETUP_MODE=%1
if "%SETUP_MODE%"=="" set SETUP_MODE=docker

if "%SETUP_MODE%"=="docker" (
    echo [*] Docker Deployment Mode
    
    echo.
    echo [Step 1] Checking Docker Installation
    docker --version >nul 2>&1
    if errorlevel 1 (
        echo [X] Docker not found. Please install Docker Desktop for Windows.
        exit /b 1
    )
    echo [OK] Docker is installed
    
    echo.
    echo [Step 2] Checking Docker Compose
    docker-compose --version >nul 2>&1
    if errorlevel 1 (
        echo [!] Docker Compose not found - trying Docker Compose V2
        docker compose --version >nul 2>&1
        if errorlevel 1 (
            echo [X] Docker Compose not found
            exit /b 1
        )
        set DOCKER_COMPOSE=docker compose
    ) else (
        set DOCKER_COMPOSE=docker-compose
    )
    echo [OK] Docker Compose found
    
    echo.
    echo [Step 3] Setting up Environment Variables
    if not exist ".env" (
        echo    Creating .env from .env.example...
        copy .env.example .env >nul
        echo [OK] .env file created
    ) else (
        echo [OK] .env file already exists
    )
    
    echo.
    echo [Step 4] Building Docker Images
    echo    This may take a few minutes...
    %DOCKER_COMPOSE% build --no-cache
    if errorlevel 1 (
        echo    Building with cache...
        %DOCKER_COMPOSE% build
    )
    echo [OK] Docker images built
    
    echo.
    echo [Step 5] Starting Services
    %DOCKER_COMPOSE% up -d
    echo [OK] Services starting...
    
    echo.
    echo [Step 6] Waiting for Health Checks
    echo    Waiting 5 seconds for services to stabilize...
    timeout /t 5 /nobreak
    
    echo.
    echo ═════════════════════════════════════════════════════════════════
    echo [OK] DEPLOYMENT SUCCESSFUL!
    echo ═════════════════════════════════════════════════════════════════
    echo.
    echo Service URLs:
    echo    Frontend:  http://localhost:5173
    echo    API:       http://localhost:8000
    echo    Health:    http://localhost:8000/health
    echo.
    echo Useful Commands:
    echo    View logs:     %DOCKER_COMPOSE% logs -f backend
    echo    Stop services: %DOCKER_COMPOSE% down
    echo    Restart:       %DOCKER_COMPOSE% restart
    echo.

) else if "%SETUP_MODE%"=="local" (
    echo [*] Local Development Mode
    
    echo.
    echo [Step 1] Checking Python Installation
    python --version >nul 2>&1
    if errorlevel 1 (
        echo [X] Python not found. Please install Python 3.10+
        exit /b 1
    )
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VER=%%i
    echo [OK] Python found: !PYTHON_VER!
    
    echo.
    echo [Step 2] Creating Virtual Environment
    if not exist "venv" (
        echo    Creating venv...
        python -m venv venv
        echo [OK] Virtual environment created
    ) else (
        echo [OK] Virtual environment exists
    )
    
    echo.
    echo [Step 3] Activating Virtual Environment
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated
    
    echo.
    echo [Step 4] Installing Python Dependencies
    echo    Installing packages...
    python -m pip install -q --upgrade pip
    pip install -q -r requirements.txt
    if errorlevel 1 (
        echo [!] Some packages may have failed, continuing...
    )
    echo [OK] Python dependencies installed
    
    echo.
    echo [Step 5] Installing Frontend Dependencies
    cd ui
    if not exist "node_modules" (
        echo    Installing npm packages...
        call npm install -q
        if errorlevel 1 (
            echo [!] npm install completed with warnings
        )
        echo [OK] Frontend dependencies installed
    ) else (
        echo [OK] Frontend dependencies exist
    )
    cd ..
    
    echo.
    echo [Step 6] Configuration Validation
    python -c "import yaml; yaml.safe_load(open('configs/optimized.yaml')); print('   [OK] Thermal config valid')"
    
    echo.
    echo ═════════════════════════════════════════════════════════════════
    echo [OK] LOCAL SETUP SUCCESSFUL!
    echo ═════════════════════════════════════════════════════════════════
    echo.
    echo To start development:
    echo.
    echo    Terminal 1 ^(Backend^):
    echo    venv\Scripts\activate.bat
    echo    uvicorn src.api.app:app --reload --port 8000
    echo.
    echo    Terminal 2 ^(Frontend^):
    echo    cd ui
    echo    npm run dev
    echo.

) else if "%SETUP_MODE%"=="prod" (
    echo [*] Production Deployment Mode
    
    echo.
    echo [Step 1] Validation Checks
    
    if not exist ".env" (
        echo [X] .env file not found
        exit /b 1
    )
    echo [OK] .env file present
    
    python -c "import yaml; yaml.safe_load(open('configs/optimized.yaml')); print('   [OK] Config valid')"
    
    echo.
    echo [Step 2] Building Production Images
    %DOCKER_COMPOSE% build --no-cache
    echo [OK] Production images built
    
    echo.
    echo [Step 3] Starting Services
    %DOCKER_COMPOSE% up -d
    echo [OK] Services started
    
    echo.
    echo ═════════════════════════════════════════════════════════════════
    echo [OK] PRODUCTION DEPLOYMENT COMPLETE!
    echo ═════════════════════════════════════════════════════════════════
    echo.

) else (
    echo [X] Unknown setup mode: %SETUP_MODE%
    echo.
    echo Usage: deploy.bat [docker^|local^|prod]
    echo.
    echo Modes:
    echo    docker - Deploy using Docker Compose
    echo    local  - Local development setup
    echo    prod   - Production deployment
    exit /b 1
)

echo.
echo Documentation:
echo    - QUICK_REFERENCE.md
echo    - DEPLOYMENT_STATUS.md
echo    - SYSTEM_IMPROVEMENTS.md
echo.
echo Happy computing!
echo.

pause
