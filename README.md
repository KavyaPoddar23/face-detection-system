# Real-Time Face Detection Video Streaming System

A containerised full-stack app that takes a live webcam feed, detects faces, draws bounding boxes, stores the data in PostgreSQL, and streams everything back to the browser in real time.

**Frontend** → React + TypeScript served via nginx  
**Backend** → Python FastAPI with WebSocket support  
**Face Detection** → face_recognition + Pillow (no OpenCV used)  
**Database** → PostgreSQL storing ROI coordinates per frame  
**Infrastructure** → Docker + Docker Compose  

## Quick Start

You need Docker Desktop installed and a webcam. That's it.

```bash
git clone <your-repo-url>
cd face-detection-system
docker-compose up --build
```

First run takes about 2 minutes. Once all three containers are up:

- Frontend → http://localhost:3000
- Backend API → http://localhost:8000
- API Docs → http://localhost:8000/docs

Open localhost:3000, click **Start Stream**, allow camera access, and you'll see a green box around your face. ROI data gets stored in the database automatically.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | /api/stream/input | Receives raw frames from the browser |
| WS | /api/stream/output | Serves processed frames to viewers |
| GET | /api/roi | Returns stored ROI records from the database |
| GET | /health | Health check |

Query the ROI endpoint with an optional session filter:
```
GET /api/roi?session_id=abc-123&limit=50
```

## Database Schema

The rois table stores one record per detected face per frame:

```
id            serial primary key
session_id    varchar  (groups frames from one stream session)
frame_number  integer
x, y          float    (top-left corner of bounding box)
width, height float    (bounding box dimensions)
confidence    float
timestamp     timestamptz
```

## Project Structure

```
face-detection-system/
├── backend/
│   ├── app/
│   │   ├── api/routes.py
│   │   ├── core/config.py
│   │   ├── db/models.py
│   │   ├── services/face_detection.py
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/VideoStream.tsx
│   │   └── services/websocket.ts
│   ├── nginx.conf
│   └── Dockerfile
├── docs/architecture.png
├── docker-compose.yml
└── README.md
```

## Running Tests

```bash
docker exec face_detection_backend python -m pytest tests/ -v
```

19 tests pass covering the face detection service and all API endpoints.

## Stopping

```bash
docker-compose down
```

Remove the database volume too:

```bash
docker-compose down -v
```

## AI Collaboration

AI tools were used in a limited capacity during this project, primarily for understanding errors and looking up syntax.

The overall system design, architecture decisions, technology choices, and implementation were done independently. This includes deciding on the three-endpoint WebSocket structure, designing the database schema, building the face detection pipeline without OpenCV, setting up the Docker Compose configuration, and writing the frontend streaming logic.

Where AI came in was mostly for debugging — when a Docker build failed due to a dependency conflict, AI helped understand the error message and pointed toward which package was causing the issue. Similarly, for a couple of Python and TypeScript errors during development, AI was used to quickly understand what the error meant rather than spending time digging through documentation.

The code was written, tested, and verified manually throughout. Every part of the system was run and confirmed working end-to-end before being committed.