import { useEffect, useRef } from 'react';

interface FaceScanOverlayProps {
  videoStream: MediaStream | null;
  message?: string;
}

export default function FaceScanOverlay({ videoStream, message }: FaceScanOverlayProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current && videoStream) {
      videoRef.current.srcObject = videoStream;
      videoRef.current.play();
    }
  }, [videoStream]);

  return (
    <div className="face-scan-overlay">
      <div className="face-scan-container">
        <div className="scan-header">
          <h3>📸 Face Recognition</h3>
          <p>{message || 'Position your face in the frame'}</p>
        </div>
        
        <div className="video-container">
          <video 
            ref={videoRef} 
            autoPlay 
            playsInline 
            muted
            className="face-video"
          />
          <div className="face-frame">
            <div className="corner top-left"></div>
            <div className="corner top-right"></div>
            <div className="corner bottom-left"></div>
            <div className="corner bottom-right"></div>
          </div>
        </div>

        <div className="scan-status">
          <div className="pulse-dot"></div>
          <span>Scanning...</span>
        </div>
      </div>
    </div>
  );
}
