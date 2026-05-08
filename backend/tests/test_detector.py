"""
Unit tests for detector.py drawing and result logic.

We mock the MediaPipe detector so these tests run without a GPU or model file,
and focus on what we own: the bounding-box drawing and DetectionResult contract.
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from app.detector import DetectionResult, _BOX_COLOR, _BOX_WIDTH, detect_and_annotate


def _blank_jpeg(width: int = 320, height: int = 240) -> bytes:
    """Create a plain grey JPEG in memory — no real face needed."""
    img = Image.new("RGB", (width, height), color=(128, 128, 128))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _make_mock_detection(x: int, y: int, w: int, h: int, score: float):
    """Build a fake MediaPipe detection result."""
    bbox = MagicMock()
    bbox.origin_x = x
    bbox.origin_y = y
    bbox.width    = w
    bbox.height   = h

    category = MagicMock()
    category.score = score

    detection = MagicMock()
    detection.bounding_box = bbox
    detection.categories   = [category]

    result = MagicMock()
    result.detections = [detection]
    return result


class TestDetectAndAnnotate:
    def test_no_face_returns_original_bytes(self):
        """When no face is detected the original JPEG bytes are returned unchanged."""
        jpeg = _blank_jpeg()
        empty_result = MagicMock()
        empty_result.detections = []

        with patch("app.detector._detector") as mock_det:
            mock_det.detect.return_value = empty_result
            out_bytes, roi = detect_and_annotate(jpeg)

        assert out_bytes == jpeg
        assert roi.face_found is False
        assert roi.x == 0 and roi.y == 0 and roi.width == 0 and roi.height == 0
        assert roi.confidence is None

    def test_face_found_sets_face_found_true(self):
        jpeg = _blank_jpeg()
        mock_result = _make_mock_detection(10, 20, 80, 60, 0.92)

        with patch("app.detector._detector") as mock_det:
            mock_det.detect.return_value = mock_result
            _, roi = detect_and_annotate(jpeg)

        assert roi.face_found is True
        assert roi.x == 10
        assert roi.y == 20
        assert roi.width == 80
        assert roi.height == 60

    def test_confidence_is_rounded_to_4dp(self):
        jpeg = _blank_jpeg()
        mock_result = _make_mock_detection(0, 0, 50, 50, 0.876543)

        with patch("app.detector._detector") as mock_det:
            mock_det.detect.return_value = mock_result
            _, roi = detect_and_annotate(jpeg)

        assert roi.confidence == round(0.876543, 4)

    def test_annotated_output_is_valid_jpeg(self):
        jpeg = _blank_jpeg()
        mock_result = _make_mock_detection(10, 10, 50, 50, 0.9)

        with patch("app.detector._detector") as mock_det:
            mock_det.detect.return_value = mock_result
            out_bytes, _ = detect_and_annotate(jpeg)

        # Should be decodable as an image
        img = Image.open(io.BytesIO(out_bytes))
        assert img.format == "JPEG"

    def test_bounding_box_pixel_is_green(self):
        """The top-left corner pixel of the box should be the BOX_COLOR."""
        jpeg = _blank_jpeg(320, 240)
        x, y, w, h = 50, 40, 100, 80
        mock_result = _make_mock_detection(x, y, w, h, 0.95)

        with patch("app.detector._detector") as mock_det:
            mock_det.detect.return_value = mock_result
            out_bytes, _ = detect_and_annotate(jpeg)

        img = Image.open(io.BytesIO(out_bytes)).convert("RGB")
        # Sample a pixel on the top edge of the box
        pixel = img.getpixel((x + w // 2, y))
        # Allow JPEG compression artefacts (±60 per channel)
        for got, want in zip(pixel, _BOX_COLOR):
            assert abs(got - want) < 60, f"pixel {pixel} != expected ~{_BOX_COLOR}"

    def test_bbox_clipped_to_image_bounds(self):
        """Bounding box that exceeds image dimensions should be clipped."""
        width, height = 320, 240
        jpeg = _blank_jpeg(width, height)
        # MediaPipe returns a box that overflows the image
        mock_result = _make_mock_detection(300, 220, 200, 200, 0.8)

        with patch("app.detector._detector") as mock_det:
            mock_det.detect.return_value = mock_result
            _, roi = detect_and_annotate(jpeg)

        assert roi.x + roi.width  <= width
        assert roi.y + roi.height <= height

    def test_detection_result_is_frozen(self):
        roi = DetectionResult(x=1, y=2, width=3, height=4, confidence=0.9, face_found=True)
        with pytest.raises(Exception):
            roi.x = 99  # frozen dataclass must raise
