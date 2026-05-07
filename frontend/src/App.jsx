import { useMemo } from "react";
import { VideoPane } from "./components/VideoPane.jsx";
import { RoiTable } from "./components/RoiTable.jsx";
import { useStream } from "./hooks/useStream.js";
import { useRoi } from "./hooks/useRoi.js";

// Generate one UUID per page load — ties together the ingest + feed + ROI queries
function newSessionId() {
  return crypto.randomUUID();
}

export default function App() {
  const sessionId  = useMemo(newSessionId, []);
  const { feedSrc, status, start, stop } = useStream(sessionId);
  const detections = useRoi(sessionId, status === "live");

  return (
    <>
      <h1>Real-Time Face Detection</h1>
      <p className="session-id">Session: {sessionId}</p>
      <div className="layout">
        <VideoPane
          feedSrc={feedSrc}
          status={status}
          onStart={start}
          onStop={stop}
        />
        <RoiTable detections={detections} />
      </div>
    </>
  );
}
