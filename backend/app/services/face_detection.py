import mediapipe as mp
import numpy as np
from PIL import Image, ImageDraw
import io
import base64
from typing import Optional, Tuple

# Initialize mediapipe face detection
mp_face_detection = mp.solutions.face_detection

class FaceDetectionService:
    def __init__(self):
        self.face_detection = mp_face_detection.FaceDetection(
            model_selection=0,       # 0 = short range (within 2m), best for webcam
            min_detection_confidence=0.5
        )

    def detect_and_draw(
        self,
        frame_bytes: bytes,
        frame_number: int = 0
    ) -> Tuple[bytes, Optional[dict]]:
        """
        Takes raw image bytes, detects face, draws ROI box.
        Returns (processed_image_bytes, roi_data_dict)
        """
        # Step 1: Open image using Pillow (NO OpenCV)
        image = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
        width, height = image.size

        # Step 2: Convert to numpy array for mediapipe
        frame_array = np.array(image)

        # Step 3: Run face detection
        results = self.face_detection.process(frame_array)

        roi_data = None

        # Step 4: If face detected, draw bounding box using Pillow
        if results.detections:
            detection = results.detections[0]  # Only one face assumed
            bbox = detection.location_data.relative_bounding_box

            # Convert relative coordinates to absolute pixel values
            x = int(bbox.xmin * width)
            y = int(bbox.ymin * height)
            w = int(bbox.width * width)
            h = int(bbox.height * height)

            # Clamp values to image boundaries
            x = max(0, x)
            y = max(0, y)
            w = min(w, width - x)
            h = min(h, height - y)

            # Step 5: Draw rectangle using Pillow ImageDraw (NO OpenCV)
            draw = ImageDraw.Draw(image)
            draw.rectangle(
                [x, y, x + w, y + h],
                outline=(0, 255, 0),   # Green color
                width=3
            )

            # Step 6: Store ROI data
            roi_data = {
                "frame_number": frame_number,
                "x": float(x),
                "y": float(y),
                "width": float(w),
                "height": float(h),
                "confidence": float(detection.score[0])
            }

        # Step 7: Convert processed image back to bytes
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=85)
        processed_bytes = output_buffer.getvalue()

        return processed_bytes, roi_data


    def decode_base64_frame(self, base64_string: str) -> bytes:
        """
        Converts a base64 encoded frame (from browser webcam) to bytes
        """
        # Remove data URL prefix if present
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        return base64.b64decode(base64_string)


    def encode_frame_to_base64(self, frame_bytes: bytes) -> str:
        """
        Converts processed frame bytes to base64 string to send back to browser
        """
        return base64.b64encode(frame_bytes).decode("utf-8")


# Single instance to reuse across requests (efficient)
face_detection_service = FaceDetectionService()