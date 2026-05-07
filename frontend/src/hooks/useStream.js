/**
 * useStream — manages the full webcam → ingest WS → feed WS pipeline.
 *
 * Returns:
 *   feedSrc   : string | null  — object URL of the latest annotated frame
 *   status    : "idle" | "live" | "error"
 *   start()   : open webcam, connect both WebSockets, begin streaming
 *   stop()    : close everything
 */

import { useCallback, useRef, useState } from "react";

const WS_BASE = import.meta.env.VITE_WS_URL ?? "";
const FRAME_INTERVAL_MS = 100; // ~10 fps — adjust as needed

export function useStream(sessionId) {
  const [status, setStatus]       = useState("idle");
  const [feedSrc, setFeedSrc]     = useState(null);
  const [frameCount, setFrameCount] = useState(0);

  const ingestWsRef  = useRef(null);
  const feedWsRef    = useRef(null);
  const streamRef    = useRef(null);   // MediaStream
  const intervalRef  = useRef(null);
  const canvasRef    = useRef(null);
  const prevBlobUrl  = useRef(null);

  const stop = useCallback(() => {
    clearInterval(intervalRef.current);

    ingestWsRef.current?.close();
    feedWsRef.current?.close();
    streamRef.current?.getTracks().forEach((t) => t.stop());

    ingestWsRef.current = null;
    feedWsRef.current   = null;
    streamRef.current   = null;

    if (prevBlobUrl.current) {
      URL.revokeObjectURL(prevBlobUrl.current);
      prevBlobUrl.current = null;
    }
    setFeedSrc(null);
    setFrameCount(0);
    setStatus("idle");
  }, []);

  const start = useCallback(async () => {
    try {
      // 1. Get webcam
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;

      // 2. Hidden video element to draw frames onto canvas
      const video = document.createElement("video");
      video.srcObject = stream;
      video.muted = true;
      await video.play();

      // 3. Canvas for JPEG encoding
      const canvas = document.createElement("canvas");
      canvas.width  = video.videoWidth  || 640;
      canvas.height = video.videoHeight || 480;
      canvasRef.current = canvas;
      const ctx = canvas.getContext("2d");

      // 4. Open ingest WebSocket
      const ingestWs = new WebSocket(`${WS_BASE}/ws/ingest/${sessionId}`);
      ingestWs.binaryType = "arraybuffer";
      ingestWsRef.current = ingestWs;

      await new Promise((res, rej) => {
        ingestWs.onopen  = res;
        ingestWs.onerror = rej;
      });

      // 5. Open feed WebSocket
      const feedWs = new WebSocket(`${WS_BASE}/ws/feed/${sessionId}`);
      feedWs.binaryType = "blob";
      feedWsRef.current = feedWs;

      feedWs.onmessage = (evt) => {
        const url = URL.createObjectURL(evt.data);
        setFeedSrc((prev) => {
          if (prevBlobUrl.current) URL.revokeObjectURL(prevBlobUrl.current);
          prevBlobUrl.current = url;
          return url;
        });
        setFrameCount((n) => n + 1);
      };

      feedWs.onerror = () => setStatus("error");

      // 6. Capture + send loop
      intervalRef.current = setInterval(() => {
        if (ingestWs.readyState !== WebSocket.OPEN) return;
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob(
          (blob) => {
            if (!blob) return;
            blob.arrayBuffer().then((buf) => ingestWs.send(buf));
          },
          "image/jpeg",
          0.8
        );
      }, FRAME_INTERVAL_MS);

      setStatus("live");
    } catch (err) {
      console.error("Stream error:", err);
      stop();
      setStatus("error");
    }
  }, [sessionId, stop]);

  return { feedSrc, status, frameCount, start, stop };
}
