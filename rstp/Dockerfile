FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including OpenCV requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-dev \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Install Flask and OpenCV
RUN pip install --no-cache-dir \
    flask==3.0.0 \
    flask-cors==4.0.0 \
    opencv-python-headless==4.10.0.84 \
    numpy==2.0.2

# Copy application code
COPY rtsp_webcam_server.py /app/rtsp_webcam_server.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["python", "rtsp_webcam_server.py"]