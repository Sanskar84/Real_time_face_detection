export function VideoPane({ feedSrc, status, frameCount, lastConf, onStart, onStop }) {
  const confPct = lastConf != null ? (lastConf * 100).toFixed(1) + "%" : "—";

  return (
    <div className="card">
      <div className="card-header">
        <h2>Annotated Feed</h2>
        <span className={`badge ${status}`}>
          <span className={`dot ${status === "live" ? "pulse" : ""}`} />
          {status.toUpperCase()}
        </span>
      </div>

      <div className="video-wrap">
        {feedSrc ? (
          <img src={feedSrc} alt="Annotated video feed" />
        ) : (
          <div className="video-placeholder">
            {/* camera outline icon */}
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
              <circle cx="12" cy="13" r="4"/>
            </svg>
            <p>Press Start to begin streaming</p>
          </div>
        )}
      </div>

      <div className="stats-bar">
        <div className="stat">
          <span className="stat-label">Frames</span>
          <span className="stat-value">{frameCount}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Last Confidence</span>
          <span className="stat-value">{confPct}</span>
        </div>
        <div className="stat">
          <span className="stat-label">Target FPS</span>
          <span className="stat-value">10</span>
        </div>
      </div>

      <div className="controls">
        <button className="btn-start" onClick={onStart} disabled={status === "live"}>
          ▶ Start
        </button>
        <button className="btn-stop" onClick={onStop} disabled={status !== "live"}>
          ■ Stop
        </button>
      </div>
    </div>
  );
}
