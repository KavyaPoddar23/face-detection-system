import React, { useRef, useEffect, useState, useCallback } from 'react';
import { VideoStreamService } from '../services/websocket';

interface ROIData {
  frame_number: number;
  x: number;
  y: number;
  width: number;
  height: number;
  confidence: number;
}

const VideoStream: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const displayCanvasRef = useRef<HTMLCanvasElement>(null);
  const streamServiceRef = useRef<VideoStreamService | null>(null);
  const animationRef = useRef<number | undefined>(undefined);
  const isStreamingRef = useRef(false);

  const [isStreaming, setIsStreaming] = useState(false);
  const [roiData, setRoiData] = useState<ROIData | null>(null);
  const [processedFrame, setProcessedFrame] = useState<string | null>(null);
  const [faceDetected, setFaceDetected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Handle processed frame from backend
  const handleProcessedFrame = useCallback((data: any) => {
    if (data.processed_frame) {
      setProcessedFrame(data.processed_frame);
    }
    if (data.roi) {
      setRoiData(data.roi);
      setFaceDetected(true);
    } else {
      setFaceDetected(false);
    }
  }, []);

  // Draw processed frame on display canvas
  useEffect(() => {
    if (!processedFrame || !displayCanvasRef.current) return;
    const canvas = displayCanvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
    };
    img.src = `data:image/jpeg;base64,${processedFrame}`;
  }, [processedFrame]);

  // Capture and send frames to backend
  const captureAndSendFrame = useCallback(() => {
    if (
      !isStreamingRef.current ||
      !videoRef.current ||
      !canvasRef.current
    ) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    // Get frame as base64
    const base64Frame = canvas.toDataURL('image/jpeg', 0.8);
    streamServiceRef.current?.sendFrame(base64Frame);

    // Continue capturing at ~15fps
    animationRef.current = setTimeout(
      () => requestAnimationFrame(captureAndSendFrame),
      66
    ) as unknown as number;
  }, []);

  // Start streaming
  const startStream = async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 }
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      // Connect WebSocket
      streamServiceRef.current = new VideoStreamService(handleProcessedFrame);
      streamServiceRef.current.connect();

      // Wait a moment for WebSocket to connect
      await new Promise(resolve => setTimeout(resolve, 500));

      isStreamingRef.current = true;
      setIsStreaming(true);
      requestAnimationFrame(captureAndSendFrame);

    } catch (err: any) {
      setError(`Failed to start stream: ${err.message}`);
    }
  };

  // Stop streaming
  const stopStream = () => {
    isStreamingRef.current = false;
    setIsStreaming(false);

    if (animationRef.current) {
      clearTimeout(animationRef.current);
    }

    streamServiceRef.current?.disconnect();

    if (videoRef.current?.srcObject) {
      const tracks = (videoRef.current.srcObject as MediaStream).getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }

    setProcessedFrame(null);
    setRoiData(null);
    setFaceDetected(false);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => stopStream();
  }, []);

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>🎯 Real-Time Face Detection</h1>

      {error && (
        <div style={styles.error}>{error}</div>
      )}

      <div style={styles.videoGrid}>
        {/* Original webcam feed (hidden, used for capture) */}
        <video
          ref={videoRef}
          style={{ display: 'none' }}
          muted
          playsInline
        />

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />

        {/* Processed video display */}
        <div style={styles.videoWrapper}>
          <h3 style={styles.videoLabel}>Processed Feed</h3>
          <canvas
            ref={displayCanvasRef}
            style={styles.videoCanvas}
          />
          {!processedFrame && (
            <div style={styles.placeholder}>
              {isStreaming ? 'Waiting for frames...' : 'Start stream to begin'}
            </div>
          )}
        </div>

        {/* ROI Data Panel */}
        <div style={styles.roiPanel}>
          <h3 style={styles.videoLabel}>ROI Data</h3>

          <div style={{
            ...styles.statusBadge,
            backgroundColor: faceDetected ? '#00ff88' : '#ff4444'
          }}>
            {faceDetected ? '✅ Face Detected' : '❌ No Face'}
          </div>

          {roiData && (
            <div style={styles.roiData}>
              <div style={styles.roiRow}>
                <span style={styles.roiLabel}>Frame</span>
                <span style={styles.roiValue}>#{roiData.frame_number}</span>
              </div>
              <div style={styles.roiRow}>
                <span style={styles.roiLabel}>X</span>
                <span style={styles.roiValue}>{roiData.x.toFixed(1)}px</span>
              </div>
              <div style={styles.roiRow}>
                <span style={styles.roiLabel}>Y</span>
                <span style={styles.roiValue}>{roiData.y.toFixed(1)}px</span>
              </div>
              <div style={styles.roiRow}>
                <span style={styles.roiLabel}>Width</span>
                <span style={styles.roiValue}>{roiData.width.toFixed(1)}px</span>
              </div>
              <div style={styles.roiRow}>
                <span style={styles.roiLabel}>Height</span>
                <span style={styles.roiValue}>{roiData.height.toFixed(1)}px</span>
              </div>
              <div style={styles.roiRow}>
                <span style={styles.roiLabel}>Confidence</span>
                <span style={styles.roiValue}>
                  {(roiData.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Controls */}
      <div style={styles.controls}>
        {!isStreaming ? (
          <button onClick={startStream} style={styles.startButton}>
            ▶ Start Stream
          </button>
        ) : (
          <button onClick={stopStream} style={styles.stopButton}>
            ⏹ Stop Stream
          </button>
        )}
      </div>
    </div>
  );
};

// Styles
const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#0f0f1a',
    color: 'white',
    padding: '20px',
    fontFamily: 'Arial, sans-serif',
  },
  title: {
    textAlign: 'center',
    fontSize: '2rem',
    marginBottom: '20px',
    color: '#00ff88',
  },
  error: {
    backgroundColor: '#ff444433',
    border: '1px solid #ff4444',
    borderRadius: '8px',
    padding: '10px 20px',
    marginBottom: '20px',
    textAlign: 'center',
  },
  videoGrid: {
    display: 'flex',
    gap: '20px',
    justifyContent: 'center',
    flexWrap: 'wrap',
    marginBottom: '20px',
  },
  videoWrapper: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    backgroundColor: '#1a1a2e',
    borderRadius: '12px',
    padding: '15px',
    border: '1px solid #333',
  },
  videoLabel: {
    marginBottom: '10px',
    color: '#aaa',
    fontSize: '0.9rem',
  },
  videoCanvas: {
    width: '640px',
    maxWidth: '90vw',
    height: 'auto',
    borderRadius: '8px',
    backgroundColor: '#000',
  },
  placeholder: {
    width: '640px',
    maxWidth: '90vw',
    height: '480px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#111',
    borderRadius: '8px',
    color: '#555',
  },
  roiPanel: {
    backgroundColor: '#1a1a2e',
    borderRadius: '12px',
    padding: '15px',
    border: '1px solid #333',
    minWidth: '220px',
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  statusBadge: {
    padding: '8px 16px',
    borderRadius: '20px',
    textAlign: 'center',
    color: '#000',
    fontWeight: 'bold',
    fontSize: '0.9rem',
  },
  roiData: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    marginTop: '10px',
  },
  roiRow: {
    display: 'flex',
    justifyContent: 'space-between',
    borderBottom: '1px solid #333',
    paddingBottom: '6px',
  },
  roiLabel: {
    color: '#888',
    fontSize: '0.85rem',
  },
  roiValue: {
    color: '#00ff88',
    fontWeight: 'bold',
    fontSize: '0.85rem',
  },
  controls: {
    display: 'flex',
    justifyContent: 'center',
    gap: '10px',
  },
  startButton: {
    backgroundColor: '#00ff88',
    color: '#000',
    border: 'none',
    padding: '12px 40px',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  stopButton: {
    backgroundColor: '#ff4444',
    color: '#fff',
    border: 'none',
    padding: '12px 40px',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
};

export default VideoStream;