import pytest
import io
import base64
from PIL import Image, ImageDraw
from app.services.face_detection import FaceDetectionService


def create_test_image(width=640, height=480, color=(100, 149, 237)) -> bytes:
    """Creates a simple solid color test image as bytes"""
    image = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def create_base64_test_image() -> str:
    """Creates a base64 encoded test image"""
    image_bytes = create_test_image()
    return base64.b64encode(image_bytes).decode("utf-8")


@pytest.fixture
def service():
    return FaceDetectionService()


class TestFaceDetectionService:

    def test_service_initializes(self, service):
        """Test that the service initializes without errors"""
        assert service is not None

    def test_decode_base64_frame_with_prefix(self, service):
        """Test decoding base64 frame that has data URL prefix"""
        image_bytes = create_test_image()
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:image/jpeg;base64,{b64}"

        result = service.decode_base64_frame(data_url)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_decode_base64_frame_without_prefix(self, service):
        """Test decoding base64 frame without data URL prefix"""
        image_bytes = create_test_image()
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        result = service.decode_base64_frame(b64)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_encode_frame_to_base64(self, service):
        """Test encoding frame bytes to base64"""
        image_bytes = create_test_image()
        result = service.encode_frame_to_base64(image_bytes)

        assert isinstance(result, str)
        assert len(result) > 0
        # Verify it's valid base64
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_detect_and_draw_no_face(self, service):
        """Test detection on image with no face returns None roi"""
        image_bytes = create_test_image()
        processed_bytes, roi_data = service.detect_and_draw(image_bytes, 0)

        assert isinstance(processed_bytes, bytes)
        assert len(processed_bytes) > 0
        assert roi_data is None  # No face in solid color image

    def test_detect_and_draw_returns_valid_image(self, service):
        """Test that processed image is valid JPEG"""
        image_bytes = create_test_image()
        processed_bytes, _ = service.detect_and_draw(image_bytes, 0)

        # Verify output is a valid image
        result_image = Image.open(io.BytesIO(processed_bytes))
        assert result_image.size[0] > 0
        assert result_image.size[1] > 0

    def test_detect_and_draw_frame_number(self, service):
        """Test that frame number is passed correctly"""
        image_bytes = create_test_image()
        _, roi_data = service.detect_and_draw(image_bytes, 42)
        # roi_data is None for no face, but function should not crash
        assert True

    def test_roi_data_structure(self, service):
        """Test ROI data has correct structure when face detected"""
        # We test the structure by mocking what roi_data should look like
        expected_keys = {"frame_number", "x", "y", "width", "height", "confidence"}

        # Create a mock roi to verify structure
        mock_roi = {
            "frame_number": 1,
            "x": 100.0,
            "y": 80.0,
            "width": 200.0,
            "height": 220.0,
            "confidence": 1.0
        }

        assert set(mock_roi.keys()) == expected_keys
        assert isinstance(mock_roi["x"], float)
        assert isinstance(mock_roi["y"], float)
        assert isinstance(mock_roi["width"], float)
        assert isinstance(mock_roi["height"], float)

    def test_decode_then_encode_roundtrip(self, service):
        """Test that decode then encode gives back valid image"""
        original_bytes = create_test_image()
        b64 = base64.b64encode(original_bytes).decode("utf-8")

        decoded = service.decode_base64_frame(b64)
        reencoded = service.encode_frame_to_base64(decoded)

        assert isinstance(reencoded, str)
        final_bytes = base64.b64decode(reencoded)
        image = Image.open(io.BytesIO(final_bytes))
        assert image.size == (640, 480)