-- init.sql
-- Runs once when the Postgres container starts for the first time.

-- Each processed video frame gets a row here.
CREATE TABLE IF NOT EXISTS frames (
    id          BIGSERIAL    PRIMARY KEY,
    session_id  UUID         NOT NULL,          -- groups frames from one streaming session
    frame_seq   INTEGER      NOT NULL,          -- 0-based frame number within the session
    captured_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    UNIQUE (session_id, frame_seq)
);

-- The axis-aligned bounding box (ROI) detected in a frame.
-- One face per frame, so one row per frame.
CREATE TABLE IF NOT EXISTS roi_detections (
    id          BIGSERIAL    PRIMARY KEY,
    frame_id    BIGINT       NOT NULL REFERENCES frames(id) ON DELETE CASCADE,
    x           INTEGER      NOT NULL,   -- left edge in pixels
    y           INTEGER      NOT NULL,   -- top  edge in pixels
    width       INTEGER      NOT NULL,   -- box width  in pixels
    height      INTEGER      NOT NULL,   -- box height in pixels
    confidence  REAL,                    -- detector confidence score (0–1), nullable if not available
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Speed up the common query: "give me all ROIs for a session ordered by frame"
CREATE INDEX IF NOT EXISTS idx_roi_frame_id ON roi_detections(frame_id);
CREATE INDEX IF NOT EXISTS idx_frames_session ON frames(session_id, frame_seq);
