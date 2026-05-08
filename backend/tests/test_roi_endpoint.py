"""
Integration tests for GET /roi/{session_id}.

Uses an in-memory SQLite database (aiosqlite) so no real Postgres is needed.
The FastAPI app's get_db dependency is overridden for the duration of each test.
"""

import uuid
from datetime import datetime

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models import Frame, RoiDetection

# ── In-memory SQLite engine shared across tests in a session ─────────────────
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, scope="module")
async def create_tables():
    """Create all tables once before the test module runs, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Yield a test DB session and roll back after each test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session):
    """AsyncClient with the get_db dependency overridden to use test DB."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _insert_frame_with_roi(db: AsyncSession, session_id: str, frame_seq: int,
                                  x=10, y=20, w=80, h=60, conf=0.9):
    frame = Frame(session_id=session_id, frame_seq=frame_seq, captured_at=datetime.utcnow())
    db.add(frame)
    await db.flush()
    db.add(RoiDetection(frame_id=frame.id, x=x, y=y, width=w, height=h, confidence=conf))
    await db.commit()
    return frame


# ── Tests ────────────────────────────────────────────────────────────────────

class TestGetRoi:
    async def test_unknown_session_returns_404(self, client):
        resp = await client.get(f"/roi/{uuid.uuid4()}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    async def test_session_with_no_detections_returns_empty_list(self, client, db_session):
        session_id = str(uuid.uuid4())
        # Insert a frame but NO roi row — simulates frames with no face detected
        frame = Frame(session_id=session_id, frame_seq=0, captured_at=datetime.utcnow())
        db_session.add(frame)
        await db_session.commit()

        resp = await client.get(f"/roi/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["detections"] == []

    async def test_returns_roi_data_for_known_session(self, client, db_session):
        session_id = str(uuid.uuid4())
        await _insert_frame_with_roi(db_session, session_id, frame_seq=0,
                                     x=10, y=20, w=80, h=60, conf=0.92)

        resp = await client.get(f"/roi/{session_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        d = data["detections"][0]
        assert d["x"] == 10
        assert d["y"] == 20
        assert d["width"] == 80
        assert d["height"] == 60
        assert abs(d["confidence"] - 0.92) < 0.001

    async def test_detections_ordered_by_frame_seq(self, client, db_session):
        session_id = str(uuid.uuid4())
        # Insert out of order
        for seq in [2, 0, 1]:
            await _insert_frame_with_roi(db_session, session_id, frame_seq=seq)

        resp = await client.get(f"/roi/{session_id}")
        assert resp.status_code == 200
        seqs = [d["frame_seq"] for d in resp.json()["detections"]]
        assert seqs == sorted(seqs)

    async def test_limit_and_offset_pagination(self, client, db_session):
        session_id = str(uuid.uuid4())
        for seq in range(5):
            await _insert_frame_with_roi(db_session, session_id, frame_seq=seq)

        resp = await client.get(f"/roi/{session_id}?limit=2&offset=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["detections"][0]["frame_seq"] == 1

    async def test_health_endpoint(self, client):
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
