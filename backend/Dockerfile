# ── Stage 1: install dependencies ──────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System libs needed by MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Download the BlazeFace TFLite model (short-range, ~820 KB)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /build/app/assets \
    && curl -fsSL \
       "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite" \
       -o /build/app/assets/blaze_face_short_range.tflite


# ── Stage 2: lean runtime image ─────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy only the installed packages from the builder stage
COPY --from=builder /install /usr/local
# Copy the downloaded model asset
COPY --from=builder /build/app/assets/ ./app/assets/
# System libs needed at runtime by MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY app/ ./app/

# Run as non-root for security
RUN adduser --disabled-password --gecos "" appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
