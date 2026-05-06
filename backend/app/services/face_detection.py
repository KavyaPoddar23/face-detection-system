import face_recognition
import numpy as np
from PIL import Image, ImageDraw
import io
import base64
from typing import Optional, Tuple


class FaceDetectionService:
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

        # Step 2: Convert to numpy array for face_recognition
        frame_array = np.array(image)

        # Step 3: Detect face locations
        face_locations = face_recognition.face_locations(frame_array, model="hog")

        roi_data = None

        # Step 4: If face detected, draw bounding box using Pillow
        if face_locations:
            # face_locations returns (top, right, bottom, left)
            top, right, bottom, left = face_locations[0]

            x = left
            y = top
            w = right - left
            h = bottom - top

            # Step 5: Draw rectangle using Pillow ImageDraw (NO OpenCV)
            draw = ImageDraw.Draw(image)
            draw.rectangle(
                [x, y, x + w, y + h],
                outline=(0, 255, 0),
                width=3
            )

            roi_data = {
                "frame_number": frame_number,
                "x": float(x),
                "y": float(y),
                "width": float(w),
                "height": float(h),
                "confidence": 1.0
            }

        # Step 6: Convert processed image back to bytes
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=85)
        processed_bytes = output_buffer.getvalue()

        return processed_bytes, roi_data

    def decode_base64_frame(self, base64_string: str) -> bytes:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        return base64.b64decode(base64_string)

    def encode_frame_to_base64(self, frame_bytes: bytes) -> str:
        return base64.b64encode(frame_bytes).decode("utf-8")


face_detection_service = FaceDetectionService()