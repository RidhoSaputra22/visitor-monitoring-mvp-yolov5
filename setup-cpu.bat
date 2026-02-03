@echo off
setlocal

echo Setting up CPU-only Visitor Monitoring system...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo Error: Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Copy CPU environment file
if exist ".env.cpu" (
    copy ".env.cpu" ".env" >nul
    echo Using CPU-only environment configuration
) else (
    echo CPU environment file not found. Using default configuration...
)

echo Building and starting services with CPU-only support...

REM Stop any existing services
docker-compose down

REM Pull latest images
docker-compose pull

REM Build with no cache
docker-compose build --no-cache

REM Start services
docker-compose up -d

echo Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Check service health
echo Checking service health...
docker-compose ps

echo.
echo Setup complete! Access the application at:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:8000
echo - RTSP Stream: http://localhost:8080/video
echo.
echo Default login credentials:
echo - Username: admin
echo - Password: admin123
echo.
echo To view logs: docker-compose logs -f
echo To stop services: docker-compose down

pause