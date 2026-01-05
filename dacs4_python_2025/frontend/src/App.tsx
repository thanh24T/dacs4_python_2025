import { useState, useRef, useEffect, useCallback } from 'react';
import RegistrationForm from './components/RegistrationForm';
import SettingsModal from './components/SettingsModal';
import FaceScanOverlay from './components/FaceScanOverlay';
import ReminderModal from './components/ReminderModal';
import ReminderNotification from './components/ReminderNotification';

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

interface User {
  id: number;
  username: string;
  full_name: string;
  gender: string;
  age: number;
  avatar_url?: string;
}

interface Reminder {
  id: number;
  title: string;
  description?: string;
  reminder_time: string;
  is_completed: boolean;
}

function App() {
  const [isReady, setIsReady] = useState(false);
  const [userName, setUserName] = useState<string>('');
  const [userEmotion, setUserEmotion] = useState<string>('');
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [showRegistrationForm, setShowRegistrationForm] = useState(false);
  const [registerName, setRegisterName] = useState<string>('');
  const [hasGreeted, setHasGreeted] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  
  // Chat history
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [showSettings, setShowSettings] = useState(false);
  const [showFaceScan, setShowFaceScan] = useState(false);
  const [faceScanMessage, setFaceScanMessage] = useState('Position your face in the frame');
  const [videoStream, setVideoStream] = useState<MediaStream | null>(null);
  
  // Reminders
  const [showReminders, setShowReminders] = useState(false);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [showReminderNotification, setShowReminderNotification] = useState(false);
  const [reminderNotificationData, setReminderNotificationData] = useState<any>(null);
  
  const orbRef = useRef<HTMLDivElement>(null);

  // Refs quản lý Audio
  const socketRef = useRef<WebSocket | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animationFrameRef = useRef<number>(0);

  // Hàng đợi âm thanh
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const isPlayingRef = useRef(false);

  // Visualizer loop
  const animateOrb = useCallback(() => {
    if (!analyserRef.current || !orbRef.current) return;

    const analyser = analyserRef.current;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);

    let sum = 0;
    const relevantFreqs = dataArray.slice(0, 50);
    for (let i = 0; i < relevantFreqs.length; i++) {
      sum += relevantFreqs[i];
    }

    let volume = (sum / relevantFreqs.length) / 100.0;
    if (volume > 1.2) volume = 1.2;
    if (volume < 0.1) volume = 0.0;

    orbRef.current?.style.setProperty('--volume-level', volume.toFixed(3));
    animationFrameRef.current = requestAnimationFrame(animateOrb);
  }, []);

  // Process audio queue
  const processAudioQueue = async () => {
    if (isPlayingRef.current || (audioQueueRef.current?.length || 0) === 0 || !audioContextRef.current) return;

    isPlayingRef.current = true;
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

  // Initialize system
  const initializeAudio = async () => {
    try {
      console.log("🚀 Đang khởi tạo hệ thống...");

      const AudioContext = window.AudioContext || (window as any).webkitAudioContext;
      const audioCtx = new AudioContext();
      audioContextRef.current = audioCtx;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.5;
      analyserRef.current = analyser;

      try {
        // Video stream for face recognition
        const videoStream = await navigator.mediaDevices.getUserMedia({ 
          audio: false,
          video: true
        });
        
        setVideoStream(videoStream); // Store for preview
        setShowFaceScan(true); // Show camera preview
        setFaceScanMessage('Scanning for face...');
        
        // Auto-hide camera preview after 10 seconds if no recognition
        setTimeout(() => {
          if (showFaceScan) {
            setShowFaceScan(false);
            console.log('[TIMEOUT] Face scan timeout - hiding camera');
          }
        }, 10000);
        
        // Audio stream for mic
        const audioStream = await navigator.mediaDevices.getUserMedia({
          audio: true,
          video: false
        });
        
        const micSource = audioCtx.createMediaStreamSource(audioStream);
        micSource.connect(analyser);
        
        // Start face recognition (hidden)
        startFaceRecognition(videoStream);
        
      } catch (err) {
        console.warn("Không lấy được quyền Micro/Camera:", err);
      }

      connectWebSocket(audioCtx);
      animateOrb();
      setIsReady(true);

    } catch (err) {
      console.error("Lỗi khởi tạo:", err);
      alert("Lỗi: " + err);
    }
  };

  // Face recognition (hidden video)
  const startFaceRecognition = (stream: MediaStream) => {
    const canvas = document.createElement('canvas');
    const video = document.createElement('video');
    video.srcObject = stream;
    video.play();
    
    // Hidden video element
    video.style.display = 'none';
    document.body.appendChild(video);

    let recognitionAttempts = 0;
    const maxAttempts = 5; // Try 5 times (10 seconds)

    const intervalId = setInterval(() => {
      if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
        console.log('[FACE] WebSocket not ready, skipping...');
        return;
      }

      if (recognitionAttempts >= maxAttempts) {
        console.log('[FACE] Max attempts reached, stopping...');
        clearInterval(intervalId);
        setShowFaceScan(false);
        setFaceScanMessage('Face recognition timeout. Please try again.');
        return;
      }

      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      if (canvas.width === 0 || canvas.height === 0) {
        console.log('[FACE] Video not ready yet...');
        return;
      }

      canvas.getContext('2d')?.drawImage(video, 0, 0);

      canvas.toBlob((blob) => {
        if (blob && socketRef.current) {
          console.log(`[FACE] Sending image attempt ${recognitionAttempts + 1}/${maxAttempts}...`);
          socketRef.current.send(blob);
          recognitionAttempts++;
          setFaceScanMessage(`Scanning... (${recognitionAttempts}/${maxAttempts})`);
        }
      }, 'image/jpeg', 0.8);
    }, 2000);
  };

  // WebSocket connection
  const connectWebSocket = (audioCtx: AudioContext) => {
    const wsUrl = 'ws://localhost:8765';
    const ws = new WebSocket(wsUrl);
    socketRef.current = ws;
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      console.log("✅ Đã kết nối tới Brain!");
      // Don't load conversations here - will be loaded after login
    };
    
    ws.onclose = () => console.log("❌ Mất kết nối Brain");

    ws.onmessage = async (event) => {
      if (typeof event.data === 'string') {
        try {
          const data = JSON.parse(event.data);
          console.log('[WS] Received message:', data.type); // ✅ Debug log
          
          if (data.type === 'show_registration') {
            // New user detected - show registration form
            console.log('[WS] Showing registration form');
            setShowFaceScan(false); // Hide camera preview
            setShowRegistrationForm(true);
          } else if (data.type === 'hide_registration') {
            // Hide registration form immediately (user recognized)
            console.log('[WS] Hiding registration form');
            setShowRegistrationForm(false);
            setShowFaceScan(false);
          } else if (data.type === 'user_logged_in') {
            // Existing user auto-login
            console.log('[WS] User logged in:', data.user.username);
            console.log('[WS] Conversations received:', data.conversations);
            setShowFaceScan(false); // Hide camera preview
            setShowRegistrationForm(false); // Ensure registration form is hidden
            setCurrentUser(data.user);
            setUserName(data.user.username);
            setConversations(data.conversations);
            setShowRegistrationForm(false);
            setHasGreeted(true);
            // Don't call loadConversations() - already have conversations from backend
          } else if (data.type === 'registration_success') {
            // Registration completed
            setShowFaceScan(false); // Hide camera preview
            setCurrentUser(data.user);
            setUserName(data.user.username);
            setCurrentConversationId(data.conversation_id);
            setShowRegistrationForm(false);
            setHasGreeted(true);
            addMessage('assistant', data.message);
          } else if (data.type === 'registration_failed') {
            alert(data.message);
          } else if (data.type === 'greeting') {
            setShowFaceScan(false); // Hide camera after greeting
            addMessage('assistant', data.content);
            if (data.user) {
              setUserName(data.user);
              // If greeting has user info, try to get full user data
              if (!currentUser) {
                // Request user data from server or set basic info
                console.log('[GREETING] User detected:', data.user);
              }
            }
            if (data.emotion) setUserEmotion(data.emotion);
            setHasGreeted(true);
          } else if (data.type === 'emotion_update') {
            if (data.emotion) setUserEmotion(data.emotion);
            if (data.user) setUserName(data.user);
          } else if (data.type === 'user_text') {
            addMessage('user', data.content);
          } else if (data.type === 'text') {
            addMessage('assistant', data.content);
          } else if (data.type === 'reminders') {
            setReminders(data.reminders);
          } else if (data.type === 'reminder_created') {
            console.log('[REMINDER] Created:', data.reminder_id);
          } else if (data.type === 'reminder_notification') {
            // Show fullscreen notification
            console.log('[REMINDER] Notification:', data.reminder.title);
            const isMissed = data.is_missed || false;
            setReminderNotificationData({
              title: isMissed ? `⚠️ Missed: ${data.reminder.title}` : data.reminder.title,
              description: data.reminder.description
            });
            setShowReminderNotification(true);
            
            // Also add to chat if missed
            if (isMissed) {
              addMessage('assistant', data.message);
            }
          } else if (data.type === 'reminder_completed') {
            // Refresh reminders
            if (socketRef.current && currentUser) {
              socketRef.current.send(JSON.stringify({ type: 'get_reminders' }));
            }
          } else if (data.type === 'reminder_deleted') {
            // Refresh reminders
            if (socketRef.current && currentUser) {
              socketRef.current.send(JSON.stringify({ type: 'get_reminders' }));
            }
          } else if (data.type === 'conversations') {
            setConversations(data.conversations);
          } else if (data.type === 'title_updated') {
            // Auto-refresh conversations when title is updated
            console.log('[WS] Title updated:', data.title);
            loadConversations();
          } else if (data.type === 'conversation_created') {
            setCurrentConversationId(data.conversation_id);
            loadConversations();
          } else if (data.type === 'messages') {
            setMessages(data.messages);
          }
        } catch(e) {}
      } else if (event.data instanceof ArrayBuffer) {
        try {
          const audioBuffer = await audioCtx.decodeAudioData(event.data);
          audioQueueRef.current.push(audioBuffer);
          processAudioQueue();
        } catch (err) {
          console.error("Lỗi decode audio:", err);
        }
      }
    };
  };
  
  // Load conversations
  const loadConversations = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN && currentUser) {
      socketRef.current.send(JSON.stringify({
        type: 'get_conversations'
      }));
    }
  };
  
  // Mute/Unmute mic
  const muteMic = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'mute_mic' }));
    }
  };

  const unmuteMic = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: 'unmute_mic' }));
    }
  };
  
  // Create new conversation
  const createNewConversation = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN && currentUser) {
      // If current conversation has messages, request title generation
      if (currentConversationId && messages.length >= 2) {
        socketRef.current.send(JSON.stringify({
          type: 'generate_title',
          conversation_id: currentConversationId
        }));
      }
      
      // Stop any ongoing audio playback
      audioQueueRef.current = [];
      isPlayingRef.current = false;
      
      // Clear messages and reset state
      setMessages([]);
      setCurrentConversationId(null);
      setHasGreeted(false); // Reset to require new greeting
      
      // Notify backend to reset greeting state
      socketRef.current.send(JSON.stringify({
        type: 'reset_greeting'
      }));
      
      // Send create conversation request
      socketRef.current.send(JSON.stringify({
        type: 'create_conversation',
        title: 'New Chat'
      }));
      
      console.log('[NEW CHAT] Created new conversation, voice chat paused');
    }
  };
  
  // Load conversation messages
  const loadConversation = (conversationId: number) => {
    setCurrentConversationId(conversationId);
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'get_messages',
        conversation_id: conversationId
      }));
    }
  };
  
  // Add message
  const addMessage = (role: 'user' | 'assistant', content: string) => {
    const newMessage: Message = {
      role,
      content,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, newMessage]);
  };

  // Register user (new method with full form)
  const handleRegisterUser = (regData: any) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'register_user',
        ...regData
      }));
    }
  };
  
  // Register user (old method - simple name)
  const handleRegisterUserSimple = () => {
    if (!registerName.trim()) {
      alert("Please enter your name!");
      return;
    }

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({
        type: 'register_user_old',
        name: registerName.trim()
      }));
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      if (socketRef.current) socketRef.current.close();
      if (audioContextRef.current) audioContextRef.current.close();
      if (animationFrameRef.current) cancelAnimationFrame(animationFrameRef.current);
    };
  }, []);

  return (
    <div className="app-container">
      {/* SIDEBAR - Chat History (Always Open) */}
      <div className="sidebar open">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={createNewConversation}>
            ✏️ New Chat
          </button>
          <button 
            className="reminder-btn" 
            onClick={() => {
              muteMic(); // Mute mic before opening
              if (socketRef.current && currentUser) {
                socketRef.current.send(JSON.stringify({ type: 'get_reminders' }));
              }
              setShowReminders(true);
            }}
            title="AI Reminders"
          >
            🔔
          </button>
        </div>
        
        <div className="conversations-list">
          <div className="section-title">My Chats</div>
          {conversations.map(conv => (
            <div 
              key={conv.id}
              className={`conversation-item ${currentConversationId === conv.id ? 'active' : ''}`}
              onClick={() => loadConversation(conv.id)}
            >
              <div className="conv-title">{conv.title}</div>
              <div className="conv-date">{new Date(conv.updated_at).toLocaleDateString()}</div>
            </div>
          ))}
        </div>
        
        <div className="sidebar-footer">
          {currentUser ? (
            <div className="user-profile" onClick={() => setShowSettings(true)}>
              <div className="user-avatar">
                {currentUser.avatar_url ? (
                  <img src={currentUser.avatar_url} alt={currentUser.username} />
                ) : (
                  <div className="avatar-placeholder">
                    {currentUser.username.charAt(0).toUpperCase()}
                  </div>
                )}
              </div>
              <div className="user-details">
                <div className="user-name">{currentUser.full_name}</div>
                <div className="user-status">
                  {userEmotion && <span className="emotion-badge">{userEmotion}</span>}
                  <span className="settings-hint">⚙️ Settings</span>
                </div>
              </div>
            </div>
          ) : (
            isReady && (
              <div className="user-profile-placeholder">
                <div className="pulse-dot"></div>
                <span>Waiting for face recognition...</span>
              </div>
            )
          )}
        </div>
      </div>

      {/* MAIN CONTENT - Orb + Messages */}
      <div className="main-content">
        {/* Messages Display */}
        <div className="messages-container">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-content">{msg.content}</div>
            </div>
          ))}
        </div>

        {/* Voice Orb */}
        <div className="orb-container">
          <div className="voice-orb-wrapper" onClick={!isReady ? initializeAudio : undefined}>
            <div ref={orbRef} className={`orb-core ${!isReady ? 'inactive' : ''}`}></div>
            <div className={`orb-glow ${!isReady ? 'inactive' : ''}`}></div>
            {!isReady && <div className="click-hint">CLICK TO START</div>}
          </div>
          
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
      </div>

      {/* Face Scan Overlay */}
      {showFaceScan && videoStream && (
        <FaceScanOverlay
          videoStream={videoStream}
          message={faceScanMessage}
        />
      )}

      {/* Settings Modal */}
      {showSettings && currentUser && (
        <SettingsModal
          user={currentUser}
          onClose={() => setShowSettings(false)}
          onLogout={() => {
            setCurrentUser(null);
            setUserName('');
            setShowSettings(false);
            setHasGreeted(false);
            setMessages([]);
            // Reload page to restart face recognition
            window.location.reload();
          }}
        />
      )}

      {/* Registration Form (New User) */}
      {showRegistrationForm && (
        <RegistrationForm
          onRegister={handleRegisterUser}
          onCancel={() => setShowRegistrationForm(false)}
        />
      )}

      {/* Registration Modal (Simple - Old Method) */}
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
              onKeyDown={(e) => e.key === 'Enter' && handleRegisterUserSimple()}
              autoFocus
            />
            <div className="modal-buttons">
              <button onClick={handleRegisterUserSimple}>Register</button>
              <button onClick={() => setShowRegisterModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* Reminder Modal */}
      {showReminders && (
        <ReminderModal
          reminders={reminders}
          onClose={() => {
            setShowReminders(false);
            unmuteMic(); // Unmute when closing
          }}
          onCreateReminder={(data) => {
            socketRef.current?.send(JSON.stringify({
              type: 'create_reminder',
              ...data
            }));
          }}
          onCompleteReminder={(id) => {
            socketRef.current?.send(JSON.stringify({
              type: 'complete_reminder',
              reminder_id: id
            }));
          }}
          onDeleteReminder={(id) => {
            socketRef.current?.send(JSON.stringify({
              type: 'delete_reminder',
              reminder_id: id
            }));
          }}
        />
      )}

      {/* Reminder Notification Fullscreen */}
      {showReminderNotification && reminderNotificationData && (
        <ReminderNotification
          title={reminderNotificationData.title}
          description={reminderNotificationData.description}
          onDismiss={() => {
            setShowReminderNotification(false);
            setReminderNotificationData(null);
          }}
        />
      )}
    </div>
  );
}

export default App;
