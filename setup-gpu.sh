#!/bin/bash

# Setup script for GPU-enabled Docker environment

echo "Setting up GPU-enabled Visitor Monitoring system..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if NVIDIA Docker runtime is available
if ! docker info | grep -q nvidia; then
    echo "Warning: NVIDIA Docker runtime not detected. GPU features may not work."
    echo "Please install nvidia-docker2 for GPU support."
fi

# Copy GPU environment file
if [ -f ".env.gpu" ]; then
    cp .env.gpu .env
    echo "Using GPU environment configuration"
else
    echo "GPU environment file not found. Creating one..."
    cat > .env.gpu << 'EOL'
# Backend
APP_ENV=production
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/visitors
REDIS_URL=redis://cache:6379/0
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Single camera (optional default RTSP)
DEFAULT_CAMERA_NAME=Kamera Utama
DEFAULT_CAMERA_RTSP=rtsp://user:pass@ip:554/stream

# Edge
EDGE_MODE=real           # fake | real
EDGE_CAMERA_ID=1
EDGE_POST_INTERVAL_SECONDS=3
EDGE_CONFIG_REFRESH_SECONDS=30
EDGE_RTSP_URL=http://rtsp-server:8080/video

# YOLOv5 settings (GPU)
YOLOV5_CONF=0.35
YOLOV5_IOU=0.45
YOLOV5_IMG_SIZE=640
YOLOV5_DEVICE=cuda:0     # GPU enabled
YOLOV5_REPO=ultralytics/yolov5
YOLOV5_WEIGHTS=yolov5s.pt
EOL
    cp .env.gpu .env
fi

echo "Building and starting services with GPU support..."

# Build and start services
docker-compose -f docker-compose.gpu.yml down
docker-compose -f docker-compose.gpu.yml pull
docker-compose -f docker-compose.gpu.yml build --no-cache
docker-compose -f docker-compose.gpu.yml up -d

echo "Waiting for services to be ready..."
sleep 30

# Check service health
echo "Checking service health..."
docker-compose -f docker-compose.gpu.yml ps

echo ""
echo "Setup complete! Access the application at:"
echo "- Frontend: http://localhost:3000"
echo "- Backend API: http://localhost:8000"
echo "- RTSP Stream: http://localhost:8080/video"
echo ""
echo "Default login credentials:"
echo "- Username: admin"
echo "- Password: admin123"
echo ""
echo "To view logs: docker-compose -f docker-compose.gpu.yml logs -f"
echo "To stop services: docker-compose -f docker-compose.gpu.yml down"
