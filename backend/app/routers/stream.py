"""
WebSocket endpoints for video streaming.

WS /ws/ingest/{session_id}
    - Client sends raw JPEG bytes frame by frame.
    - Backend runs face detection, stores ROI in DB, pushes annotated frame
      into a per-session asyncio.Queue.

WS /ws/feed/{session_id}
    - Frontend connects and receives annotated JPEG bytes from the queue.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.detector import detect_and_annotate
from app.models import Frame, RoiDetection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["stream"])

# Per-session queues: session_id → asyncio.Queue of annotated JPEG bytes.
# Using maxsize to apply backpressure if the feed consumer is slow.
_queues: dict[str, asyncio.Queue[bytes]] = defaultdict(lambda: asyncio.Queue(maxsize=30))


@router.websocket("/ingest/{session_id}")
async def ingest(websocket: WebSocket, session_id: str):
    """
    Receive JPEG frames from the client, detect faces, persist ROIs, and
    forward annotated frames to the feed queue for this session.
    """
    await websocket.accept()
    queue = _queues[session_id]
    frame_seq = 0

    try:
        while True:
            jpeg_bytes = await websocket.receive_bytes()

            # --- face detection + annotation (CPU-bound but fast enough) ----
            annotated, roi = detect_and_annotate(jpeg_bytes)

            # --- persist to DB only if a face was detected ------------------
            if roi.face_found:
                async with AsyncSessionLocal() as db:
                    frame = Frame(session_id=session_id, frame_seq=frame_seq)
                    db.add(frame)
                    await db.flush()  # get frame.id without committing yet

                    db.add(RoiDetection(
                        frame_id=frame.id,
                        x=roi.x,
                        y=roi.y,
                        width=roi.width,
                        height=roi.height,
                        confidence=roi.confidence,
                    ))
                    await db.commit()

            # --- push annotated frame to the feed queue ---------------------
            # drop frame if queue is full (backpressure) rather than blocking
            try:
                queue.put_nowait(annotated)
            except asyncio.QueueFull:
                logger.debug("Feed queue full for session %s — dropping frame", session_id)

            frame_seq += 1

    except WebSocketDisconnect:
        logger.info("Ingest disconnected: session=%s frames=%d", session_id, frame_seq)
    finally:
        # Signal feed consumers that the stream is over
        try:
            queue.put_nowait(b"")
        except asyncio.QueueFull:
            pass


@router.websocket("/feed/{session_id}")
async def feed(websocket: WebSocket, session_id: str):
    """
    Stream annotated JPEG frames to the frontend.
    An empty bytes payload signals end-of-stream.
    """
    await websocket.accept()
    queue = _queues[session_id]

    try:
        while True:
            frame = await queue.get()
            if frame == b"":
                # End-of-stream sentinel — close gracefully
                break
            await websocket.send_bytes(frame)

    except WebSocketDisconnect:
        logger.info("Feed consumer disconnected: session=%s", session_id)
