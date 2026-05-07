from datetime import datetime

from pydantic import BaseModel


class RoiOut(BaseModel):
    id: int
    frame_id: int
    frame_seq: int
    x: int
    y: int
    width: int
    height: int
    confidence: float | None
    captured_at: datetime

    model_config = {"from_attributes": True}


class RoiListOut(BaseModel):
    session_id: str
    total: int
    detections: list[RoiOut]
