import cv2
from flask import Flask, Response

app = Flask(__name__)

cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # CAP_DSHOW lebih stabil di Windows
if not cap.isOpened():
    raise RuntimeError("Webcam tidak terbuka. Coba ganti index (0/1) atau cek izin kamera Windows.")

def gen():
    while True:
        ok, frame = cap.read()
        if not ok:
            continue
        ok, jpg = cv2.imencode(".jpg", frame)
        if not ok:
            continue
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")

@app.get("/video")
def video():
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    # akses dari container: http://host.docker.internal:8080/video
    app.run(host="0.0.0.0", port=8080, threaded=True)
