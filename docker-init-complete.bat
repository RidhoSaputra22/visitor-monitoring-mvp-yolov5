@echo off
echo ========================================
echo   Docker Initialization Complete!
echo ========================================
echo.

echo Your Visitor Monitoring system is ready to use!
echo.

echo Available setup options:
echo.
echo   1. CPU-only setup (Recommended for development):
echo      setup-cpu.bat
echo.
echo   2. GPU-enabled setup (For production with NVIDIA GPU):  
echo      setup-gpu.bat
echo.
echo   3. Manual setup:
echo      docker-compose up --build
echo.

echo Services that will be available:
echo   - Frontend:     http://localhost:3000
echo   - Backend API:  http://localhost:8000/docs
echo   - Video Stream: http://localhost:8080/video
echo   - Database:     localhost:5432
echo   - Cache:        localhost:6379
echo.

echo Default login credentials:
echo   - Username: admin
echo   - Password: admin123
echo.

echo For detailed configuration, see:
echo   - README.md (Quick start guide)
echo   - DOCKER_README.md (Complete Docker documentation)
echo.

echo Files created/updated:
echo   ✓ docker-compose.yml (CPU version)
echo   ✓ docker-compose.gpu.yml (GPU version)  
echo   ✓ All Dockerfiles optimized
echo   ✓ Environment configurations (.env, .env.cpu, .env.gpu)
echo   ✓ Setup scripts (setup-cpu.bat, setup-gpu.bat)
echo   ✓ Documentation updated
echo   ✓ Health checks added
echo   ✓ Security improvements
echo.

echo Choose your setup method and run it to start the system!
echo.
pause