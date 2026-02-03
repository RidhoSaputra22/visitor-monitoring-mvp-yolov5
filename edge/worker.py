import os
import time
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
import threading

import requests
import numpy as np
import cv2
import torch
from flask import Flask, Response
from flask_cors import CORS

# Global variable for sharing latest frame with stream server
latest_frame = None
frame_lock = threading.Lock()

# Flask app for streaming
flask_app = Flask(__name__)
CORS(flask_app)

def gen_frames():
    """Generate MJPEG stream frames from shared worker frame"""
    print("[stream] Client connected to video feed")
    while True:
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()
            else:
                frame = None
        
        if frame is None:
            time.sleep(0.1)
            continue
        
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@flask_app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@flask_app.route('/health')
def health():
    return {'status': 'ok', 'camera': env("EDGE_RTSP_URL", "/dev/video0")}

def start_flask_server():
    """Start Flask server in background thread"""
    print("[stream] Starting Flask server on port 5000")
    flask_app.run(host='0.0.0.0', port=5000, threaded=True, debug=False)


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


MODE = env("EDGE_MODE", "fake").lower()
CAMERA_ID = int(env("EDGE_CAMERA_ID", "1"))

POST_INTERVAL = int(env("EDGE_POST_INTERVAL_SECONDS", "3"))
CONFIG_REFRESH = int(env("EDGE_CONFIG_REFRESH_SECONDS", "30"))

EDGE_RTSP_URL = env("EDGE_RTSP_URL", "").strip()

CONF_TH = float(env("YOLOV5_CONF", "0.35"))
IOU_TH = float(env("YOLOV5_IOU", "0.45"))
IMG_SIZE = int(env("YOLOV5_IMG_SIZE", "640"))
DEVICE = env("YOLOV5_DEVICE", "cpu")
WEIGHTS = env("YOLOV5_WEIGHTS", "").strip()
REPO = env("YOLOV5_REPO", "").strip()

TRACK_MAX_DISAPPEARED = int(env("TRACK_MAX_DISAPPEARED", "20"))
TRACK_MAX_DISTANCE = float(env("TRACK_MAX_DISTANCE", "80"))

INGEST_URL = env("BACKEND_INGEST_URL", "http://backend:8000/api/events/ingest")
AUTH_USER = env("EDGE_AUTH_USERNAME", "admin")
AUTH_PASS = env("EDGE_AUTH_PASSWORD", "admin123")
API_BASE = INGEST_URL.split("/api/")[0].rstrip("/")


def login_token() -> Optional[str]:
    try:
        r = requests.post(
            f"{API_BASE}/api/auth/login",
            json={"username": AUTH_USER, "password": AUTH_PASS},
            timeout=10,
        )
        if r.status_code == 200:
            return r.json()["access_token"]
    except Exception:
        return None
    return None


def get_camera_config(token: Optional[str]) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.get(f"{API_BASE}/api/cameras/{CAMERA_ID}", headers=headers, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


def load_yolov5_model():
    """Load YOLOv5 via torch.hub.

    Strategy:
    - If YOLOV5_REPO + YOLOV5_WEIGHTS set: load local repo (offline-friendly)
    - Else: load from ultralytics/yolov5 (needs internet first time)
    """
    if REPO and WEIGHTS:
        model = torch.hub.load(REPO, "custom", path=WEIGHTS, source="local")
    elif WEIGHTS and not REPO:
        model = torch.hub.load("ultralytics/yolov5", "custom", path=WEIGHTS)
    else:
        model = torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)

    model.conf = CONF_TH
    model.iou = IOU_TH
    model.classes = [0]  # person only
    model.to(DEVICE)
    return model


def point_in_roi(roi: Optional[List[List[float]]], x: float, y: float) -> bool:
    if not roi or len(roi) < 3:
        return True  # ROI not set => whole frame
    poly = np.array(roi, dtype=np.int32)
    return cv2.pointPolygonTest(poly, (float(x), float(y)), False) >= 0


@dataclass
class Track:
    tid: int
    centroid: Tuple[float, float]
    bbox: Tuple[float, float, float, float]  # x1,y1,x2,y2
    disappeared: int = 0
    in_roi: bool = False


class CentroidTracker:
    def __init__(self, max_disappeared: int = 20, max_distance: float = 80.0):
        self.max_disappeared = max_disappeared
        self.max_distance = max_distance
        self.next_id = 1
        self.tracks: Dict[int, Track] = {}

    def update(self, detections: List[Tuple[float, float, float, float]]) -> Dict[int, Track]:
        # no detections: age tracks
        if len(detections) == 0:
            to_del = []
            for tid, tr in self.tracks.items():
                tr.disappeared += 1
                if tr.disappeared > self.max_disappeared:
                    to_del.append(tid)
            for tid in to_del:
                del self.tracks[tid]
            return self.tracks

        det_centroids = []
        for (x1, y1, x2, y2) in detections:
            det_centroids.append(((x1 + x2) / 2.0, (y1 + y2) / 2.0))
        det_centroids = np.array(det_centroids, dtype=np.float32)

        # initialize
        if len(self.tracks) == 0:
            for i, bbox in enumerate(detections):
                c = tuple(det_centroids[i])
                tid = self.next_id
                self.next_id += 1
                self.tracks[tid] = Track(tid=tid, centroid=c, bbox=bbox)
            return self.tracks

        track_ids = list(self.tracks.keys())
        track_centroids = np.array([self.tracks[tid].centroid for tid in track_ids], dtype=np.float32)

        # distance matrix
        dists = np.linalg.norm(track_centroids[:, None, :] - det_centroids[None, :, :], axis=2)

        used_tracks = set()
        used_dets = set()

        # greedy assign smallest distances first
        for _ in range(min(dists.shape[0], dists.shape[1])):
            t_idx, d_idx = np.unravel_index(np.argmin(dists), dists.shape)
            min_dist = dists[t_idx, d_idx]
            if min_dist > self.max_distance:
                break

            tid = track_ids[t_idx]
            if tid in used_tracks or d_idx in used_dets:
                dists[t_idx, d_idx] = np.inf
                continue

            self.tracks[tid].centroid = tuple(det_centroids[d_idx])
            self.tracks[tid].bbox = detections[d_idx]
            self.tracks[tid].disappeared = 0

            used_tracks.add(tid)
            used_dets.add(d_idx)

            dists[t_idx, :] = np.inf
            dists[:, d_idx] = np.inf

        # age unmatched tracks
        to_del = []
        for tid in track_ids:
            if tid not in used_tracks:
                self.tracks[tid].disappeared += 1
                if self.tracks[tid].disappeared > self.max_disappeared:
                    to_del.append(tid)
        for tid in to_del:
            del self.tracks[tid]

        # create new tracks for unmatched detections
        for i, bbox in enumerate(detections):
            if i in used_dets:
                continue
            c = tuple(det_centroids[i])
            tid = self.next_id
            self.next_id += 1
            self.tracks[tid] = Track(tid=tid, centroid=c, bbox=bbox)

        return self.tracks


def fake_loop():
    print("[edge] running in FAKE mode")
    token = login_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    pool = [f"p{n:03d}" for n in range(1, 101)]
    while True:
        track_ids = random.sample(pool, k=random.randint(0, 6))
        count_in = random.randint(0, 3)
        count_out = random.randint(0, 2)

        payload = {
            "camera_id": CAMERA_ID,
            "ts": datetime.now(timezone.utc).isoformat(),
            "count_in": count_in,
            "count_out": count_out,
            "track_ids": track_ids,
        }
        try:
            r = requests.post(INGEST_URL, json=payload, headers=headers, timeout=10)
            print("[edge] sent", payload, "->", r.status_code)
        except Exception as e:
            print("[edge] failed to send:", e)
        time.sleep(POST_INTERVAL)


def real_loop():
    print("[edge] running in REAL mode (YOLOv5 + tracking + ROI counting)")
    token = login_token()
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    model = load_yolov5_model()
    tracker = CentroidTracker(max_disappeared=TRACK_MAX_DISAPPEARED, max_distance=TRACK_MAX_DISTANCE)

    last_cfg_fetch = 0.0
    roi = None
    rtsp_url = EDGE_RTSP_URL or ""

    batch_in = 0
    batch_out = 0
    batch_entered_ids: List[str] = []
    last_post = time.time()

    cap = None

    def open_capture(url: str):
        c = cv2.VideoCapture(url)
        c.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        return c

    while True:
        now = time.time()

        # refresh config from backend
        if now - last_cfg_fetch > CONFIG_REFRESH or last_cfg_fetch == 0:
            cfg = get_camera_config(token)
            if cfg:
                roi = cfg.get("roi")
                if not EDGE_RTSP_URL:
                    rtsp_url = (cfg.get("rtsp_url") or "").strip() or rtsp_url
            
            # Use larger default ROI for webcam resolution 1280x720
            if not roi:
                roi = [[50, 50], [1230, 50], [1230, 670], [50, 670]]  # Almost full frame
                
            last_cfg_fetch = now
            if roi:
                print("[edge] ROI loaded:", roi)
            if rtsp_url:
                print("[edge] RTSP:", rtsp_url)

        if not rtsp_url:
            print("[edge] RTSP URL not set. Set DEFAULT_CAMERA_RTSP or set via UI.")
            time.sleep(5)
            continue

        if cap is None or not cap.isOpened():
            cap = open_capture(rtsp_url)
            if not cap.isOpened():
                print("[edge] failed to open RTSP. retry...")
                try:
                    cap.release()
                except Exception:
                    pass
                cap = None
                time.sleep(3)
                continue

        ok, frame = cap.read()
        if not ok or frame is None:
            print("[edge] frame read failed. reconnect...")
            try:
                cap.release()
            except Exception:
                pass
            cap = None
            time.sleep(1)
            continue

        # Update global frame for stream server
        with frame_lock:
            global latest_frame
            latest_frame = frame.copy()

        print(f"[edge] frame captured: {frame.shape if frame is not None else 'None'}")

        # YOLO inference
        results = model(frame, size=IMG_SIZE)
        det = results.xyxy[0].detach().cpu().numpy() if hasattr(results, "xyxy") else np.zeros((0, 6), dtype=np.float32)

        print(f"[edge] YOLO detections: {len(det)} objects")

        bboxes: List[Tuple[float, float, float, float]] = []
        for x1, y1, x2, y2, conf, cls in det:
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            print(f"[edge] detected person at ({cx:.1f}, {cy:.1f}) conf={conf:.2f}")
            # Temporarily ignore ROI - accept all detections
            bboxes.append((float(x1), float(y1), float(x2), float(y2)))
            print(f"[edge] person accepted: ({cx:.1f}, {cy:.1f}) conf={conf:.2f}")

        print(f"[edge] objects in ROI: {len(bboxes)}")

        tracks = tracker.update(bboxes)

        # count transitions in/out ROI
        for tid, tr in tracks.items():
            in_roi_now = point_in_roi(roi, tr.centroid[0], tr.centroid[1])
            if (not tr.in_roi) and in_roi_now:
                batch_in += 1
                batch_entered_ids.append(f"t{tid}")
            elif tr.in_roi and (not in_roi_now):
                batch_out += 1
            tr.in_roi = in_roi_now

        # send batched event
        if now - last_post >= POST_INTERVAL:
            payload = {
                "camera_id": CAMERA_ID,
                "ts": datetime.now(timezone.utc).isoformat(),
                "count_in": batch_in,
                "count_out": batch_out,
                "track_ids": batch_entered_ids[:],
            }
            try:
                r = requests.post(INGEST_URL, json=payload, headers=headers, timeout=10)
                print("[edge] ingest", payload, "->", r.status_code)
            except Exception as e:
                print("[edge] failed to ingest:", e)

            batch_in = 0
            batch_out = 0
            batch_entered_ids = []
            last_post = now


def main():
    # Start Flask server in background thread
    flask_thread = threading.Thread(target=start_flask_server, daemon=True)
    flask_thread.start()
    print("[main] Flask streaming server started in background")
    
    # Wait a bit for Flask to start
    time.sleep(2)
    
    if MODE == "fake":
        fake_loop()
    else:
        real_loop()


if __name__ == "__main__":
    main()
