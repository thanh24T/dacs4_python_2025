# 🔧 BACKEND SERVER INTEGRATION CODE

## ✅ ĐÃ CẬP NHẬT

1. ✅ Import database module
2. ✅ Initialize database
3. ✅ Pass database to face_detector
4. ✅ Add helper functions (save_avatar, handle_registration, handle_login)

---

## 📝 CODE CẦN THÊM VÀO handle_websocket_messages

Tìm function `handle_websocket_messages` trong `server_rag.py` và thêm các handlers sau:

```python
async def handle_websocket_messages(websocket, image_queue, state):
    """Task riêng để nhận messages từ WebSocket (video frames + commands)"""
    
    # Store face image for registration
    last_face_image = None
    
    try:
        async for message in websocket:
            # 1. Xử lý JSON commands
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    cmd_type = data.get('type')
                    
                    # ========== NEW: USER REGISTRATION ==========
                    if cmd_type == 'register_user':
                        if last_face_image:
                            await handle_user_registration(websocket, data, last_face_image)
                        else:
                            await websocket.send(json.dumps({
                                'type': 'registration_failed',
                                'message': 'No face image captured. Please try again.'
                            }))
                    
                    # ========== NEW: GET CONVERSATIONS ==========
                    elif cmd_type == 'get_conversations':
                        user_id = state.get('current_user_id')
                        if user_id:
                            conversations = db.get_conversations(user_id, limit=50)
                            await websocket.send(json.dumps({
                                'type': 'conversations',
                                'conversations': [
                                    {
                                        'id': c['id'],
                                        'title': c['title'],
                                        'updated_at': c['updated_at'].isoformat() if hasattr(c['updated_at'], 'isoformat') else str(c['updated_at'])
                                    }
                                    for c in conversations
                                ]
                            }))
                    
                    # ========== NEW: GET MESSAGES ==========
                    elif cmd_type == 'get_messages':
                        conversation_id = data.get('conversation_id')
                        if conversation_id:
                            messages = db.get_messages(conversation_id)
                            await websocket.send(json.dumps({
                                'type': 'messages',
                                'messages': [
                                    {
                                        'role': m['role'],
                                        'content': m['content'],
                                        'created_at': m['created_at'].isoformat() if hasattr(m['created_at'], 'isoformat') else str(m['created_at'])
                                    }
                                    for m in messages
                                ]
                            }))
                    
                    # ========== NEW: NEW CONVERSATION ==========
                    elif cmd_type == 'new_conversation':
                        user_id = state.get('current_user_id')
                        if user_id:
                            conv_id = db.create_conversation(user_id, "New Chat")
                            await websocket.send(json.dumps({
                                'type': 'conversation_created',
                                'conversation_id': conv_id
                            }))
                            state['current_conversation_id'] = conv_id
                    
                    # ========== EXISTING: Register face (old method - keep for compatibility) ==========
                    elif cmd_type == 'register_user_old':
                        user_name = data.get('name')
                        if user_name:
                            state['register_name'] = user_name
                            state['register_mode'] = True
                            await websocket.send(json.dumps({
                                "type": "log",
                                "content": f"📸 Registration mode ON. Capturing face for '{user_name}'..."
                            }))
                            print(colorama.Fore.YELLOW + f"[REGISTER] Waiting for face capture: {user_name}" + colorama.Style.RESET_ALL)
                            
                except json.JSONDecodeError:
                    pass
            
            # 2. Xử lý image frames (bytes lớn hơn 5KB)
            elif isinstance(message, bytes) and len(message) > 5000:
                # Store for potential registration
                last_face_image = message
                
                # ========== NEW: AUTO-DETECT USER ==========
                if not state.get('user_checked'):
                    # Analyze frame (recognize user + emotion)
                    loop = asyncio.get_running_loop()
                    result = await loop.run_in_executor(
                        None,
                        face_detector.analyze_frame,
                        message
                    )
                    
                    if result['is_new_user']:
                        # New user detected - show registration form
                        print(colorama.Fore.YELLOW + "[FACE] New user detected!" + colorama.Style.RESET_ALL)
                        await websocket.send(json.dumps({
                            'type': 'show_registration',
                            'message': 'Welcome! Please register to continue.'
                        }))
                        state['user_checked'] = True
                        state['is_new_user'] = True
                    else:
                        # Existing user - auto login
                        user = result['user']
                        if user:
                            print(colorama.Fore.GREEN + f"[FACE] User recognized: {user['username']}" + colorama.Style.RESET_ALL)
                            state['current_user'] = user['username']
                            state['current_user_id'] = user['id']
                            state['user_checked'] = True
                            state['is_new_user'] = False
                            
                            # Auto login
                            await handle_user_login(websocket, user)
                            
                            # Send greeting
                            if result['greeting']:
                                await websocket.send(json.dumps({
                                    'type': 'greeting',
                                    'content': result['greeting'],
                                    'user': user['username'],
                                    'emotion': result['emotion']
                                }))
                                state['face_greeted'] = True
                
                # Continue with normal face recognition for emotion updates
                else:
                    # Đẩy vào queue để face recognition xử lý emotion
                    await image_queue.put(message)
                
    except websockets.exceptions.ConnectionClosed:
        print(colorama.Fore.YELLOW + "[WS] Connection closed" + colorama.Style.RESET_ALL)
    except Exception as e:
        print(colorama.Fore.RED + f"[WS] Error: {e}" + colorama.Style.RESET_ALL)
        traceback.print_exc()
    finally:
        # Signal face recognition to stop
        await image_queue.put(None)
```

---

## 📝 CẬP NHẬT handle_voice_chat

Thêm code để lưu messages vào database:

```python
async def handle_voice_chat(websocket, state):
    """Task riêng xử lý voice chat (VAD + STT + LLM + TTS)"""
    loop = asyncio.get_running_loop()
    
    status_text = "Đang chờ..."
    last_vol = 0
    
    try:
        while True:
            # ... existing VAD code ...
            
            # Sau khi có text từ STT
            if text:
                # ========== NEW: SAVE USER MESSAGE ==========
                conversation_id = state.get('current_conversation_id')
                if conversation_id:
                    db.add_message(
                        conversation_id=conversation_id,
                        role='user',
                        content=text,
                        user_emotion=voice_emotion or face_emotion
                    )
                
                # ... existing LLM code ...
                
                # Sau khi có response từ LLM
                if response:
                    # ========== NEW: SAVE ASSISTANT MESSAGE ==========
                    if conversation_id:
                        db.add_message(
                            conversation_id=conversation_id,
                            role='assistant',
                            content=response
                        )
                
                # ... rest of code ...
```

---

## 📝 CẬP NHẬT socket_handler

Thêm conversation_id vào state:

```python
async def socket_handler(websocket):
    """Xử lý WebSocket connection"""
    print(colorama.Fore.GREEN + f"\n[WebSocket] Client connected!" + colorama.Style.RESET_ALL)
    
    await websocket.send(json.dumps({
        "type": "log",
        "content": "✅ Connected! Voice chat + Face recognition ready..."
    }))
    
    # Shared state giữa các tasks
    state = {
        'current_user': None,
        'current_user_id': None,  # NEW
        'current_conversation_id': None,  # NEW
        'user_checked': False,  # NEW
        'is_new_user': False,  # NEW
        'face_greeted': False,
        'is_processing': False,
        'face_emotion': None,
        'voice_emotion': None,
        'register_mode': False,
        'register_name': None
    }
    
    # ... rest of code ...
```

---

## 🎯 TESTING

### **Test Flow:**

1. **Start Server:**
```bash
cd backend
python server_rag.py
```

2. **Start Frontend:**
```bash
cd frontend
npm run dev
```

3. **Open Browser:**
- Go to http://localhost:5173
- Click "CLICK TO START"
- Allow camera + mic

4. **First Time (New User):**
- Face recognition scans
- Detects new user
- Registration form appears
- Fill in details
- Click Register
- Auto login + load empty chat history

5. **Second Time (Existing User):**
- Face recognition scans
- Recognizes user
- Auto login
- Load chat history
- Greeting message

---

## 🐛 DEBUGGING

### **Check Database Connection:**
```bash
cd backend
python modules/database.py
```

### **Check Face Recognition:**
```python
from modules.face_emotion import FaceEmotionDetector
from modules.database import ChatDatabase

db = ChatDatabase()
face = FaceEmotionDetector(database=db)

# Test with image
with open('test_face.jpg', 'rb') as f:
    image_bytes = f.read()
    result = face.analyze_frame(image_bytes)
    print(result)
```

### **Server Logs:**
Watch for:
- `[DB] ✅ Connected to MySQL!`
- `[FACE] New user detected!` or `[FACE] User recognized: username`
- `[USER] ✅ Registered: username`
- `[USER] ✅ Logged in: username`

---

## ✅ CHECKLIST

- [x] Database initialized
- [x] Face detector connected to database
- [x] Helper functions added
- [ ] handle_websocket_messages updated (COPY CODE ABOVE)
- [ ] handle_voice_chat updated (COPY CODE ABOVE)
- [ ] socket_handler state updated (COPY CODE ABOVE)
- [ ] Test registration flow
- [ ] Test auto-login flow
- [ ] Test chat history saving

---

**Bạn muốn tôi tạo file server_rag_updated.py hoàn chỉnh không?**
Hoặc bạn tự copy code từ guide này vào file hiện tại?
