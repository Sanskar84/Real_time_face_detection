"""
Face detection and ROI drawing — no OpenCV.

Detection:  MediaPipe FaceDetection (BlazeFace, runs on CPU)
Drawing:    Pillow ImageDraw (axis-aligned rectangle / minimal bounding box)
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
from PIL import Image, ImageDraw

# ── Initialise MediaPipe once at module load (expensive) ─────────────────────
_base_options = mp_python.BaseOptions(
    model_asset_path="app/assets/blaze_face_short_range.tflite"
)
_detector_options = mp_vision.FaceDetectorOptions(
    base_options=_base_options,
    min_detection_confidence=0.5,
)
_detector = mp_vision.FaceDetector.create_from_options(_detector_options)

# Bounding-box colour and line thickness
_BOX_COLOR = (0, 255, 0)   # green
_BOX_WIDTH = 3             # pixels


@dataclass(frozen=True, slots=True)
class DetectionResult:
    """The axis-aligned minimal bounding box of the detected face."""
    x: int
    y: int
    width: int
    height: int
    confidence: float | None
    face_found: bool


def detect_and_annotate(jpeg_bytes: bytes) -> tuple[bytes, DetectionResult]:
    """
    Accept a JPEG frame, run face detection, draw the ROI with Pillow.

    Returns:
        annotated_jpeg: the frame with the green bounding box drawn on it
        result:         the DetectionResult (use face_found to check if a face was detected)
    """
    # --- 1. Decode bytes → PIL Image → MediaPipe Image ----------------------
    pil_img = Image.open(io.BytesIO(jpeg_bytes)).convert("RGB")
    width, height = pil_img.size

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=_pil_to_numpy(pil_img),
    )

    # --- 2. Run detection ----------------------------------------------------
    detection_result = _detector.detect(mp_image)

    if not detection_result.detections:
        # No face — return the original frame unchanged
        return jpeg_bytes, DetectionResult(
            x=0, y=0, width=0, height=0, confidence=None, face_found=False
        )

    # Problem says only one face; take the first (highest-confidence) result
    detection = detection_result.detections[0]
    bbox = detection.bounding_box

    # MediaPipe returns normalised or absolute coords depending on the task API.
    # FaceDetector Tasks API returns absolute pixel coordinates directly.
    x = max(0, bbox.origin_x)
    y = max(0, bbox.origin_y)
    w = min(bbox.width,  width  - x)
    h = min(bbox.height, height - y)

    confidence: float | None = None
    if detection.categories:
        confidence = round(float(detection.categories[0].score), 4)

    roi = DetectionResult(x=x, y=y, width=w, height=h,
                          confidence=confidence, face_found=True)

    # --- 3. Draw bounding box with Pillow ------------------------------------
    annotated = pil_img.copy()
    draw = ImageDraw.Draw(annotated)
    draw.rectangle(
        [x, y, x + w, y + h],
        outline=_BOX_COLOR,
        width=_BOX_WIDTH,
    )

    # --- 4. Re-encode to JPEG ------------------------------------------------
    buf = io.BytesIO()
    annotated.save(buf, format="JPEG", quality=85)
    return buf.getvalue(), roi


def _pil_to_numpy(img: Image.Image):
    """Convert a PIL RGB image to a numpy uint8 array without importing cv2."""
    import numpy as np
    return np.asarray(img, dtype=np.uint8)
