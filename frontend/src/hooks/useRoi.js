/**
 * useRoi — polls GET /roi/{sessionId} every 2 s while streaming is live.
 */

import { useEffect, useRef, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL ?? "";
const POLL_MS  = 2000;

export function useRoi(sessionId, active) {
  const [detections, setDetections] = useState([]);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!active) {
      setDetections([]);
      return;
    }

    const fetchRoi = async () => {
      try {
        const res = await fetch(`${API_BASE}/roi/${sessionId}`);
        if (res.ok) {
          const data = await res.json();
          setDetections(data.detections ?? []);
        }
      } catch {
        // network hiccup — silently retry next tick
      }
    };

    fetchRoi();
    timerRef.current = setInterval(fetchRoi, POLL_MS);
    return () => clearInterval(timerRef.current);
  }, [sessionId, active]);

  return detections;
}
