# Visitor Monitoring MVP (Single Camera + ROI + YOLOv5)

Cocok untuk use case skripsi kamu:
- Admin/Operator login (JWT)
- **1 kamera saja** (ID=1)
- Admin mengatur:
  - RTSP URL
  - **Area Hitung (ROI polygon)**
- Edge vision service:
  - **YOLOv5 deteksi manusia**
  - tracking sederhana (centroid tracker)
  - **menghitung saat orang MASUK ROI**
  - kirim event ke backend
- Statistik harian: total masuk/keluar + **unik (estimasi)**

## Quick Start

### Option 1: CPU-only (Recommended for development)
```bash
# Windows
setup-cpu.bat

# Linux/Mac
docker-compose up --build
```

### Option 2: GPU-enabled (For production)
```bash
# Windows
setup-gpu.bat

# Linux/Mac
./setup-gpu.sh
```

## Manual Setup

### Prerequisites
- Docker Desktop
- Docker Compose
- For GPU: NVIDIA Docker runtime

### Step 1: Choose Environment
```bash
# CPU-only (lighter, for development)
cp .env.cpu .env

# GPU-enabled (faster, for production)
cp .env.gpu .env
```

### Step 2: Run Services
```bash
# CPU version
docker-compose up --build

# GPU version
docker-compose -f docker-compose.gpu.yml up --build
```

## Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/docs
- **Video Stream**: http://localhost:8080/video

## Default Login
- Username: `admin`
- Password: `admin123`

## Services Overview

| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Next.js web interface |
| backend | 8000 | FastAPI REST API |
| edge | 5000 | YOLOv5 processing service |
| rtsp-server | 8080 | Webcam streaming |
| db | 5432 | PostgreSQL database |
| cache | 6379 | Valkey/Redis cache |

## Development

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
```

### Stop Services
```bash
docker-compose down
```

### Clean Reset
```bash
# Remove containers and volumes
docker-compose down -v

# Remove unused images
docker image prune -f
```

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Frontend   │────│   Backend   │────│  Database   │
│  (Next.js)  │    │  (FastAPI)  │    │(PostgreSQL)│
│    :3000    │    │    :8000    │    │    :5432    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           │
                   ┌─────────────┐    ┌─────────────┐
                   │    Edge     │────│ RTSP Server │
                   │  (YOLOv5)   │    │  (Webcam)   │
                   │    :5000    │    │    :8080    │
                   └─────────────┘    └─────────────┘
```

## Configuration

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker configuration options.

Open:
- Frontend: http://localhost:3000
- Swagger (API docs): http://localhost:8000/docs

Default admin:
- `admin / admin123`

## Set RTSP + Area Hitung (Admin)
1) Login
2) Buka **Konfigurasi Kamera**
3) Isi RTSP URL dan ROI (contoh):
```json
[[100,100],[500,100],[500,400],[100,400]]
```

## Jalankan YOLOv5 (REAL mode)
Di `.env`:
- set `EDGE_MODE=real`
- set RTSP via UI **atau** `DEFAULT_CAMERA_RTSP` / `EDGE_RTSP_URL`

Tuning opsional:
- `YOLOV5_DEVICE=cpu` atau `cuda:0`
- `YOLOV5_CONF=0.35`

### Catatan penting YOLOv5 weights
Edge load YOLOv5 pakai `torch.hub`:
- kalau ada internet: auto download repo/weights pertama kali
- kalau mau offline:
  - clone repo yolov5 dan mount ke container, set `YOLOV5_REPO=/yolov5`
  - taruh weights dan set `YOLOV5_WEIGHTS=/weights/yolov5s.pt`

## Aturan hitung (versi sekarang)
- Orang dihitung **1 kali masuk** ketika centroid track masuk ROI.
- `track_ids` yang masuk ROI dipakai backend untuk hitung **unik harian (estimasi)**.

Kalau kamu mau aturan **line crossing** (lebih cocok untuk pintu masuk/keluar), bilang posisi kamera & arah masuk/keluar, nanti aku ubah logikanya.
