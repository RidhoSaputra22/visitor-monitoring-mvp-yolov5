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

## Cara jalan (Docker)
```bash
docker compose up --build
```

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
