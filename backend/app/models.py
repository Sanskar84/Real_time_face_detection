import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Frame(Base):
    """One row per processed video frame."""

    __tablename__ = "frames"
    __table_args__ = (UniqueConstraint("session_id", "frame_seq"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), nullable=False)
    frame_seq: Mapped[int] = mapped_column(Integer, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    roi: Mapped["RoiDetection"] = relationship(
        "RoiDetection", back_populates="frame", uselist=False, cascade="all, delete-orphan"
    )


class RoiDetection(Base):
    """Axis-aligned bounding box (ROI) detected in a frame."""

    __tablename__ = "roi_detections"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    frame_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("frames.id", ondelete="CASCADE"), nullable=False)
    x: Mapped[int] = mapped_column(Integer, nullable=False)
    y: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    frame: Mapped["Frame"] = relationship("Frame", back_populates="roi")
