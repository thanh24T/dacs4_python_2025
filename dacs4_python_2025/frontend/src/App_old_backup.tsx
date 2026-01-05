import { useState, useRef, useEffect, useCallback } from 'react';

interface Conversation {
  id: number;
  title: string;
  updated_at: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

function App() {
  const [isReady, setIsReady] = useState(false);
  const [userName, setUserName] = useState<string>('');
  const [userEmotion, setUserEmotion] = useState<string>('');
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [registerName, setRegisterName] = useState<string>('');
  const [hasGreeted, setHasGreeted] = useState(false);
  
  // Chat history
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showSidebar, setShowSidebar] = useState(true);
  
  const orbRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null); // Hidden but still used for face recognition

  // Refs quản lý Audio
  const socketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number>(0);

  // Hàng đợi âm thanh để phát mượt mà
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);

  // --- 1. VISUALIZER LOOP (Tạo hiệu ứng rung) ---
  const animateOrb = useCallback(() => {
    if (!analyserRef.current || !orbRef.current) return;

    const analyser = analyserRef.current;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);

    // Tính độ lớn âm thanh trung bình
    let sum = 0;
    const relevantFreqs = dataArray.slice(0, 50); // Chỉ lấy dải bass/low-mid
    for (let i = 0; i < relevantFreqs.length; i++) {
      sum += relevantFreqs[i];
    }

    // Tinh chỉnh độ nhạy
    let volume = (sum / relevantFreqs.length) / 100.0;
    if (volume > 1.2) volume = 1.2;
    if (volume < 0.1) volume = 0.0;


orbRef.current?.style.setProperty('--volume-level', volume.toFixed(3));
    animationFrameRef.current = requestAnimationFrame(animateOrb);
  }, []);

  // --- 2. XỬ LÝ PHÁT ÂM THANH AI (TTS) ---
  const processAudioQueue = async () => {
    // Thêm dấu ? vào audioQueueRef.current?.length để tránh lỗi null
    if (isPlayingRef.current || (audioQueueRef.current?.length || 0) === 0 || !audioContextRef.current) return;

    isPlayingRef.current = true;

    // Thêm dấu ? vào đây nữa
    const buffer = audioQueueRef.current?.shift();

    if (buffer) {
      const source = audioContextRef.current.createBufferSource();
      source.buffer = buffer;

      if (analyserRef.current) {
        source.connect(analyserRef.current);
      }
      source.connect(audioContextRef.current.destination);

      source.onended = () => {
        isPlayingRef.current = false;
        processAudioQueue();
      };

      source.start(0);
    }
  };

  // --- 3. KHỞI TẠO HỆ THỐNG ---
  const initializeAudio = async () => {
    try {
      console.log("🚀 Đang khởi tạo hệ thống...");

      // A. Tạo AudioContext
      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioContext();
      audioContextRef.current = audioCtx;

      // B. Tạo Analyser (Bộ phân tích sóng âm)
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.5;
      analyserRef.current = analyser;

      // C. Kết nối Micro (Để quả cầu rung khi BẠN nói)
      try {
        // Lấy video stream (không có audio để tránh echo)
        const videoStream = await navigator.mediaDevices.getUserMedia({ 
          audio: false,  // Tắt audio từ webcam
          video: true
        });
        
        // Lấy audio stream riêng từ system mic
        const audioStream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: false
        });
        
        // Audio - Kết nối system mic với analyser
        const micSource = audioCtx.createMediaStreamSource(audioStream);
        micSource.connect(analyser);
        
        // Video - Hiển thị webcam
        if (videoRef.current) {
          videoRef.current.srcObject = videoStream;
        }
        
        // Gửi frame mỗi 2 giây để nhận diện
        startFaceRecognition(videoStream);
        
      } catch (err) {
        console.warn("Không lấy được quyền Micro/Camera:", err);
      }

      // D. Kết nối WebSocket
      connectWebSocket(audioCtx);

      // E. Bắt đầu vẽ hình
      animateOrb();
      setIsReady(true);

    } catch (err) {
      console.error("Lỗi khởi tạo:", err);
      alert("Lỗi: " + err);
    }
  };

  // --- 4. FACE RECOGNITION (Hidden but still running) ---
  const startFaceRecognition = (stream: MediaStream) => {
    const canvas = document.createElement('canvas');
    const video = document.createElement('video');
    video.srcObject = stream;
    video.play();
    
    // Video is hidden, only used for face recognition
    video.style.display = 'none';
    document.body.appendChild(video);

    setInterval(() => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) return;

      // Capture frame
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d')?.drawImage(video, 0, 0);

      // Convert to JPEG blob
      canvas.toBlob((blob) => {
        if (blob && socketRef.current) {
          socketRef.current.send(blob);
        }
      }, 'image/jpeg', 0.8);
    }, 2000); // Mỗi 2 giây
  };

  const connectWebSocket = (audioCtx: AudioContext) => {
      const wsUrl = 'ws://localhost:8765';
      const ws = new WebSocket(wsUrl);
      socketRef.current = ws;
      ws.binaryType = 'arraybuffer'; // Quan trọng để nhận file âm thanh

      ws.onopen = () => console.log("✅ Đã kết nối tới Brain!");
      ws.onclose = () => console.log("❌ Mất kết nối Brain");

      ws.onmessage = async (event) => {
          // 1. Nếu là LOG hoặc TEXT (Chữ)
          if (typeof event.data === 'string') {
              try {
                  const data = JSON.parse(event.data);
                  if (data.type === 'log') {
                      console.log("🤖 AI:", data.content);
                  } else if (data.type === 'greeting') {
                      // Nhận greeting từ face recognition
                      console.log("👋 Greeting:", data.content);
                      setAiText(data.content);
                      if (data.user) setUserName(data.user);
                      if (data.emotion) setUserEmotion(data.emotion);
                      setHasGreeted(true); // Đã chào hỏi → Cho phép voice chat
                  } else if (data.type === 'emotion_update') {
                      // Cập nhật emotion liên tục
                      if (data.emotion) setUserEmotion(data.emotion);
                      if (data.user) setUserName(data.user);
                  } else if (data.type === 'user_text') {
                      // Text từ STT
                      console.log("👤 User said:", data.content);
                      setUserText(data.content);
                  } else if (data.type === 'ai_text') {
                      // Response từ AI
                      console.log("🤖 AI said:", data.content);
                      setAiText(data.content);
                  } else if (data.type === 'audio') {
                      console.log("🔊 Chuẩn bị nhận audio...");
                  } else if (data.type === 'registration_success') {
                      // Đăng ký thành công
                      console.log("✅ Registration success:", data.content);
                      alert(data.content);
                      setShowRegisterModal(false);
                      setRegisterName('');
                  } else if (data.type === 'registration_failed') {
                      // Đăng ký thất bại
                      console.log("❌ Registration failed:", data.content);
                      alert(data.content);
                  }
              } catch(e) {}
          }
          // 2. Nếu là AUDIO (Bytes) -> AI đang nói
          else if (event.data instanceof ArrayBuffer) {
              console.log("🔊 Nhận tín hiệu âm thanh...");
              try {
                  // Giải mã file wav từ server
                  const audioBuffer = await audioCtx.decodeAudioData(event.data);
                  // Đẩy vào hàng đợi để phát
                  audioQueueRef.current.push(audioBuffer);
                  processAudioQueue();
              } catch (err) {
                  console.error("Lỗi decode audio:", err);
              }
          }
      };
  }

  // --- 5. USER REGISTRATION ---
  const handleRegisterUser = () => {
    if (!registerName.trim()) {
      alert("Please enter your name!");
      return;
    }

    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      alert("WebSocket not connected!");
      return;
    }

    // Gửi command đăng ký
    socketRef.current.send(JSON.stringify({
      type: 'register_user',
      name: registerName.trim()
    }));

    console.log(`📸 Registering user: ${registerName}`);
  };

  // --- 6. VOICE RECORDING ---
  const startRecording = async () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error("WebSocket chưa kết nối!");
      return;
    }

    try {
      // Lấy audio stream từ microphone
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      // Tạo MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Tạo blob từ chunks
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Convert blob to base64
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64Audio = (reader.result as string).split(',')[1];
          
          // Gửi lên server
          if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
              type: 'audio',
              data: base64Audio
            }));
            console.log("📤 Đã gửi audio lên server");
          }
        };
        reader.readAsDataURL(audioBlob);

        // Dừng stream
        stream.getTracks().forEach(track => track.stop());
      };

      // Bắt đầu ghi
      mediaRecorder.start();
      setIsRecording(true);
      console.log("🎤 Bắt đầu ghi âm...");

    } catch (err) {
      console.error("Lỗi khi ghi âm:", err);
      alert("Không thể truy cập microphone!");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      console.log("⏹️ Dừng ghi âm");
    }
  };

  // Cleanup khi tắt web
  useEffect(() => {
    return () => {
      if (socketRef.current) socketRef.current.close();
      if (audioContextRef.current) audioContextRef.current.close();
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, []);

  return (
    <>
      {/* LEFT PANEL - WEBCAM */}
      <div className="left-panel">
        <div className="webcam-container">
          <video 
            ref={videoRef} 
            className="webcam-video" 
            autoPlay 
            playsInline 
            muted
          />
          {userName && (
            <div className="webcam-overlay">
              <div>👤 {userName}</div>
              {userEmotion && <div>😊 {userEmotion}</div>}
            </div>
          )}
        </div>
        
        {/* Register Button - RA NGOÀI khung camera */}
        {!userName && isReady && (
          <button 
            className="register-btn-outside"
            onClick={() => setShowRegisterModal(true)}
          >
            📸 Register Face
          </button>
        )}
        
        {/* Voice Chat Status */}
        {isReady && (
          <div className="voice-status">
            {!hasGreeted ? (
              <div className="status-waiting">
                <div className="pulse-dot"></div>
                Waiting for greeting...
              </div>
            ) : (
              <div className="status-ready">
                <div className="ready-dot"></div>
                Voice chat ready!
              </div>
            )}
          </div>
        )}
      </div>

      {/* Registration Modal */}
      {showRegisterModal && (
        <div className="modal-overlay" onClick={() => setShowRegisterModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Register New User</h2>
            <p>Enter your name and click Register. The system will capture your face.</p>
            <input
              type="text"
              placeholder="Your name..."
              value={registerName}
              onChange={(e) => setRegisterName(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleRegisterUser()}
              autoFocus
            />
            <div className="modal-buttons">
              <button onClick={handleRegisterUser}>Register</button>
              <button onClick={() => setShowRegisterModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* RIGHT PANEL - ORB */}
      <div className="right-panel">
        <div className="voice-orb-container" onClick={!isReady ? initializeAudio : undefined}>
          {/* Quả cầu lõi */}
          <div ref={orbRef} className={`orb-core ${!isReady ? 'inactive' : ''}`}></div>
          {/* Vầng hào quang */}
          <div className={`orb-glow ${!isReady ? 'inactive' : ''}`}></div>

          {!isReady && <div className="click-hint">CLICK TO START</div>}
        </div>
      </div>
    </>
  );
}

export default App;