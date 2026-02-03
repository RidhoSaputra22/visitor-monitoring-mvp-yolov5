@echo off
setlocal

echo Setting up GPU-enabled Visitor Monitoring system...

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

REM Copy GPU environment file if exists
if exist ".env.gpu" (
    copy ".env.gpu" ".env" >nul
    echo Using GPU environment configuration
) else (
    echo GPU environment file not found. Using default configuration...
    REM Update .env for GPU usage
    powershell -Command "(Get-Content .env) -replace 'YOLOV5_DEVICE=cpu', 'YOLOV5_DEVICE=cuda:0' | Set-Content .env"
)

echo Building and starting services with GPU support...

REM Stop any existing services
docker-compose -f docker-compose.gpu.yml down

REM Pull latest images
docker-compose -f docker-compose.gpu.yml pull

REM Build with no cache
docker-compose -f docker-compose.gpu.yml build --no-cache

REM Start services
docker-compose -f docker-compose.gpu.yml up -d

echo Waiting for services to be ready...
timeout /t 30 /nobreak >nul

REM Check service health
echo Checking service health...
docker-compose -f docker-compose.gpu.yml ps

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
echo To view logs: docker-compose -f docker-compose.gpu.yml logs -f
echo To stop services: docker-compose -f docker-compose.gpu.yml down

pause