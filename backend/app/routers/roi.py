"""
REST endpoint to query stored ROI detections.

GET /roi/{session_id}          → all ROIs for a session (ordered by frame)
GET /roi/{session_id}?limit=N  → paginate
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Frame, RoiDetection
from app.schemas import RoiListOut, RoiOut

router = APIRouter(prefix="/roi", tags=["roi"])


@router.get("/{session_id}", response_model=RoiListOut)
async def get_roi(
    session_id: str,
    limit: int = Query(default=500, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Return ROI detections for a session, ordered by frame sequence."""

    stmt = (
        select(Frame, RoiDetection)
        .join(RoiDetection, RoiDetection.frame_id == Frame.id)
        .where(Frame.session_id == session_id)
        .order_by(Frame.frame_seq)
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.execute(stmt)).all()

    if not rows:
        # Session might exist but have no faces detected yet — return empty list
        # Return 404 only if the session has never been seen at all
        session_exists = await db.scalar(
            select(Frame.id).where(Frame.session_id == session_id).limit(1)
        )
        if session_exists is None:
            raise HTTPException(status_code=404, detail="Session not found")
        return RoiListOut(session_id=session_id, total=0, detections=[])

    detections = [
        RoiOut(
            id=roi.id,
            frame_id=frame.id,
            frame_seq=frame.frame_seq,
            x=roi.x,
            y=roi.y,
            width=roi.width,
            height=roi.height,
            confidence=roi.confidence,
            captured_at=frame.captured_at,
        )
        for frame, roi in rows
    ]

    return RoiListOut(
        session_id=session_id,
        total=len(detections),
        detections=detections,
    )
