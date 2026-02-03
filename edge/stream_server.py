import os
import cv2
import time
from flask import Flask, Response
from flask_cors import CORS

# Import the shared frame from worker
import sys
sys.path.insert(0, '/app')

app = Flask(__name__)
CORS(app)

EDGE_RTSP_URL = os.getenv("EDGE_RTSP_URL", "/dev/video0").strip()

def gen_frames():
    """Generate MJPEG stream frames from shared worker frame"""
    from worker import latest_frame, frame_lock
    
    print(f"[stream] Starting stream from shared frames")
    
    while True:
        # Get the latest frame from worker
        with frame_lock:
            if latest_frame is not None:
                frame = latest_frame.copy()
            else:
                frame = None
        
        if frame is None:
            # Send a placeholder frame or wait
            time.sleep(0.1)
            continue
        
        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
            
        frame_bytes = buffer.tobytes()
        
        # Yield frame in MJPEG format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    """Health check endpoint"""
    return {'status': 'ok', 'camera': EDGE_RTSP_URL}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
