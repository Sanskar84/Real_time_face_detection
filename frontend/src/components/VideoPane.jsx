export function VideoPane({ feedSrc, status, onStart, onStop }) {
  return (
    <div className="card">
      <h2>Annotated Feed</h2>
      <span className={`badge ${status}`}>{status.toUpperCase()}</span>

      <div className="video-wrap">
        {feedSrc ? (
          <img src={feedSrc} alt="Annotated video feed" />
        ) : (
          <div style={{ height: 320, display: "grid", placeItems: "center", color: "#444" }}>
            Camera feed will appear here
          </div>
        )}
      </div>

      <div className="controls">
        <button
          className="btn-start"
          onClick={onStart}
          disabled={status === "live"}
        >
          Start
        </button>
        <button
          className="btn-stop"
          onClick={onStop}
          disabled={status !== "live"}
        >
          Stop
        </button>
      </div>
    </div>
  );
}
