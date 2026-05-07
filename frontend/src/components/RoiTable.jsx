function confClass(score) {
  if (score == null) return "";
  if (score >= 0.8)  return "conf-high";
  if (score >= 0.5)  return "conf-mid";
  return "conf-low";
}

export function RoiTable({ detections }) {
  return (
    <div className="card">
      <div className="card-header">
        <h2>ROI Detections</h2>
        <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
          {detections.length} frame{detections.length !== 1 ? "s" : ""}
        </span>
      </div>

      {detections.length === 0 ? (
        <div className="empty-msg">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <path d="M3 9h18M9 21V9"/>
          </svg>
          <span>No detections yet — start the stream.</span>
        </div>
      ) : (
        <div className="roi-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Frame</th>
                <th>X</th>
                <th>Y</th>
                <th>W</th>
                <th>H</th>
                <th>Confidence</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {detections.map((d) => (
                <tr key={d.id}>
                  <td>{d.frame_seq}</td>
                  <td>{d.x}</td>
                  <td>{d.y}</td>
                  <td>{d.width}</td>
                  <td>{d.height}</td>
                  <td className={confClass(d.confidence)}>
                    {d.confidence != null ? (d.confidence * 100).toFixed(1) + "%" : "—"}
                  </td>
                  <td>{new Date(d.captured_at).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
