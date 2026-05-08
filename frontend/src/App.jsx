import { useState } from "react";
import { VideoPane } from "./components/VideoPane.jsx";
import { RoiTable } from "./components/RoiTable.jsx";
import { useStream } from "./hooks/useStream.js";
import { useRoi } from "./hooks/useRoi.js";
import { useTheme } from "./hooks/useTheme.js";

export default function App() {
  const { theme, toggle } = useTheme();
  const { sessionId, feedSrc, status, frameCount, start, stop } = useStream();
  const detections = useRoi(sessionId, status === "live");

  const [copied, setCopied] = useState(false);
  const copySession = () => {
    navigator.clipboard.writeText(sessionId);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  const lastConf = detections.at(-1)?.confidence;

  return (
    <>
      <header className="header">
        <div className="header-title">
          {/* camera icon */}
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/>
            <circle cx="12" cy="13" r="4"/>
          </svg>
          Face Detection
        </div>

        <div className="header-right">
          <div className="session-pill" title={sessionId}>
            <span>{sessionId.slice(0, 8)}…</span>
            <button className="copy-btn" onClick={copySession} title="Copy session ID">
              {copied ? "✓" : "⎘"}
            </button>
          </div>
          <button className="theme-toggle" onClick={toggle} title="Toggle theme">
            {theme === "dark" ? "☀️" : "🌙"}
          </button>
        </div>
      </header>

      <div className="layout">
        <VideoPane
          feedSrc={feedSrc}
          status={status}
          frameCount={frameCount}
          lastConf={lastConf}
          onStart={start}
          onStop={stop}
        />
        <RoiTable detections={detections} />
      </div>
    </>
  );
}
