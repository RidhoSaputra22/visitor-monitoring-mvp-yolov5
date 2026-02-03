# Visitor Monitoring System - Docker Setup

## Prerequisites

- Docker Desktop
- Docker Compose
- For GPU support: NVIDIA Docker runtime

## Quick Setup

### CPU-only setup (Recommended for development):
```bash
# Windows
setup-cpu.bat

# Linux/Mac
docker-compose up --build
```

### GPU-enabled setup (For production with NVIDIA GPU):
```bash
# Windows
setup-gpu.bat

# Linux/Mac
./setup-gpu.sh
```

## Manual Setup

### 1. Choose your environment:
```bash
# For CPU-only
cp .env.cpu .env

# For GPU-enabled
cp .env.gpu .env
```

### 2. Build and run:
```bash
# CPU version
docker-compose up --build

# GPU version
docker-compose -f docker-compose.gpu.yml up --build
```

## Services

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 3000 | Next.js web interface |
| Backend | 8000 | FastAPI REST API |
| Database | 5432 | PostgreSQL database |
| Cache | 6379 | Valkey/Redis cache |
| Edge | 5000 | YOLOv5 processing service |
| RTSP Server | 8080 | Webcam streaming server |

## Access Points

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Video Stream**: http://localhost:8080/video

## Default Credentials

- Username: `admin`
- Password: `admin123`

## Environment Configuration

### CPU vs GPU

**CPU Configuration (.env.cpu):**
- Uses YOLOv5n (nano) model for better performance
- Smaller image size (480px)
- Longer processing intervals

**GPU Configuration (.env.gpu):**
- Uses YOLOv5s (small) model
- Larger image size (640px)
- Shorter processing intervals
- Requires NVIDIA Docker runtime

### Custom Configuration

Edit the `.env` file to customize:
- Database credentials
- RTSP stream URLs
- YOLOv5 model parameters
- Processing intervals

## Docker Images Used

- `postgres:16` - Database
- `valkey/valkey:7` - Cache
- `python:3.11-slim` - Backend API
- `pytorch/pytorch:2.4.0-cuda12.1-cudnn9-runtime` - Edge processing (GPU)
- `node:20-alpine` - Frontend

## Development

### Building individual services:
```bash
# Backend
docker-compose build backend

# Frontend  
docker-compose build frontend

# Edge processing
docker-compose build edge
```

### Viewing logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Stopping services:
```bash
docker-compose down
```

### Cleaning up:
```bash
# Remove containers and networks
docker-compose down --remove-orphans

# Remove volumes (WARNING: This deletes database data)
docker-compose down -v

# Remove unused images
docker image prune -f
```

## Troubleshooting

### Common Issues:

1. **Port conflicts**: Make sure ports 3000, 8000, 5432, 6379, 5000, 8080 are available
2. **GPU not detected**: Install NVIDIA Docker runtime and verify with `nvidia-smi`
3. **Webcam access**: On Windows, may need to adjust camera index in RTSP server
4. **Slow CPU performance**: Use CPU configuration with smaller model

### Health Checks:

```bash
# Check service health
docker-compose ps

# Test API endpoint
curl http://localhost:8000/health

# Test video stream
curl http://localhost:8080/video
```

## Security Notes

- Change default passwords in production
- Use environment-specific JWT secrets
- Configure proper CORS origins
- Use SSL/TLS in production