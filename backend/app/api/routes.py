import asyncio
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.db.base import get_db
from app.db.models import ROI
from app.services.face_detection import face_detection_service
import json

router = APIRouter()

# Store active connections and processed frames
active_connections: dict = {}
processed_frames: dict = {}

# ─────────────────────────────────────────────
# ENDPOINT 1: Receive video feed from frontend
# ─────────────────────────────────────────────
@router.websocket("/stream/input")
async def stream_input(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives raw video frames from the frontend webcam.
    Processes each frame for face detection.
    Stores ROI data in the database.
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    frame_number = 0

    print(f"New input stream session: {session_id}")

    try:
        while True:
            # Receive base64 encoded frame from frontend
            data = await websocket.receive_text()
            message = json.loads(data)
            base64_frame = message.get("frame")

            if not base64_frame:
                continue

            # Decode base64 to bytes
            frame_bytes = face_detection_service.decode_base64_frame(base64_frame)

            # Detect face and draw ROI
            processed_bytes, roi_data = face_detection_service.detect_and_draw(
                frame_bytes,
                frame_number
            )

            # Store processed frame for output endpoint
            processed_frames[session_id] = {
                "frame": face_detection_service.encode_frame_to_base64(processed_bytes),
                "roi": roi_data,
                "frame_number": frame_number
            }

            # Save ROI to database if face detected
            if roi_data:
                roi_record = ROI(
                    session_id=session_id,
                    frame_number=frame_number,
                    x=roi_data["x"],
                    y=roi_data["y"],
                    width=roi_data["width"],
                    height=roi_data["height"],
                    confidence=roi_data["confidence"]
                )
                db.add(roi_record)
                await db.commit()

            # Send back processed frame + roi to frontend
            await websocket.send_text(json.dumps({
                "session_id": session_id,
                "frame_number": frame_number,
                "processed_frame": face_detection_service.encode_frame_to_base64(processed_bytes),
                "roi": roi_data
            }))

            frame_number += 1

    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
        if session_id in processed_frames:
            del processed_frames[session_id]
    except Exception as e:
        print(f"Error in stream_input: {e}")
        await websocket.close()


# ─────────────────────────────────────────────
# ENDPOINT 2: Serve processed video feed
# ─────────────────────────────────────────────
@router.websocket("/stream/output")
async def stream_output(websocket: WebSocket):
    """
    Serves the latest processed frame to any connected viewer.
    """
    await websocket.accept()
    print("Output stream connected")

    try:
        while True:
            # Send latest processed frame if available
            if processed_frames:
                latest_session = list(processed_frames.keys())[-1]
                frame_data = processed_frames[latest_session]
                await websocket.send_text(json.dumps(frame_data))
            await asyncio.sleep(0.033)  # ~30fps

    except WebSocketDisconnect:
        print("Output stream disconnected")
    except Exception as e:
        print(f"Error in stream_output: {e}")
        await websocket.close()


# ─────────────────────────────────────────────
# ENDPOINT 3: Serve ROI data from database
# ─────────────────────────────────────────────
@router.get("/roi")
async def get_roi_data(
    session_id: str = Query(None, description="Filter by session ID"),
    limit: int = Query(50, description="Number of records to return"),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns stored ROI data from the database.
    Optionally filter by session_id.
    """
    try:
        if session_id:
            query = (
                select(ROI)
                .where(ROI.session_id == session_id)
                .order_by(desc(ROI.timestamp))
                .limit(limit)
            )
        else:
            query = (
                select(ROI)
                .order_by(desc(ROI.timestamp))
                .limit(limit)
            )

        result = await db.execute(query)
        rois = result.scalars().all()

        return {
            "status": "ok",
            "count": len(rois),
            "data": [roi.to_dict() for roi in rois]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }