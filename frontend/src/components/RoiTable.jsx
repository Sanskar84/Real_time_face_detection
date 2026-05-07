export function RoiTable({ detections }) {
  return (
    <div className="card">
      <h2>ROI Detections ({detections.length})</h2>

      {detections.length === 0 ? (
        <p className="empty-msg">No detections yet — start the stream.</p>
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
                  <td>{d.confidence != null ? (d.confidence * 100).toFixed(1) + "%" : "—"}</td>
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
