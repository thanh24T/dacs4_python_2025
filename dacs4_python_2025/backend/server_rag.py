"""
WebSocket Server với RAG + Few-shot Learning
Phiên bản nâng cấp với Groq API (nhanh hơn)
"""

# Disable TensorFlow in transformers to avoid DLL issues
import os
os.environ['USE_TF'] = '0'
os.environ['USE_TORCH'] = '1'

import colorama
import torch

# Patch torch.load
try:
    _original_load = torch.load
    def _safe_load(*args, **kwargs):
        if 'weights_only' not in kwargs: kwargs['weights_only'] = False
        return _original_load(*args, **kwargs)
    torch.load = _safe_load
except:
    pass

import asyncio
import websockets
import json
import traceback
import time
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from modules.vad import VoiceDetector
from modules.stt import SpeechToText
from modules.llm_cloudflare import LLMCloudflareHandler
from modules.tts import TextToSpeech
from modules.face_emotion import FaceEmotionDetector
from modules.voice_emotion import VoiceEmotionDetector
from modules.database import ChatDatabase
from modules.reminder_scheduler import ReminderScheduler
import base64
import uuid

# Khởi tạo màu sắc
colorama.init()

print(colorama.Fore.CYAN + "=" * 80 + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "KHỞI TẠO HỆ THỐNG AI VOICE CHAT" + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "Cloudflare Workers AI + Llama 3.1 + MySQL + AI Reminders" + colorama.Style.RESET_ALL)
print(colorama.Fore.CYAN + "=" * 80 + colorama.Style.RESET_ALL)

# Khởi tạo các module
try:
    print("\n[1/8] Khởi tạo Database (MySQL)...")
    db = ChatDatabase()
    
    print("\n[2/8] Khởi tạo VAD (Voice Activity Detection)...")
    vad = VoiceDetector()
    
    print("\n[3/8] Khởi tạo STT (Speech to Text)...")
    stt = SpeechToText()
    
    print("\n[4/8] Khởi tạo LLM (Cloudflare Workers AI - Llama 3.1)...")
    llm = LLMCloudflareHandler()
    
    print("\n[5/8] Khởi tạo TTS (ElevenLabs)...")
    tts = TextToSpeech()
    
    print("\n[6/8] Khởi tạo Face Recognition + Emotion (với Database)...")
    face_detector = FaceEmotionDetector(database=db)
    
    print("\n[7/8] Khởi tạo Voice Emotion...")
    voice_detector = VoiceEmotionDetector()
    
    print("\n[8/8] Khởi tạo AI Reminder Scheduler...")
    reminder_scheduler = ReminderScheduler(db, check_interval=30)
    
except Exception as e:
    print(colorama.Fore.RED + f"\n[LỖI KHỞI TẠO] {e}" + colorama.Style.RESET_ALL)
    traceback.print_exc()
    exit(1)

print(colorama.Fore.GREEN + "\n" + "=" * 80 + colorama.Style.RESET_ALL)
print(colorama.Fore.GREEN + "HỆ THỐNG SẴN SÀNG!" + colorama.Style.RESET_ALL)
print(colorama.Fore.GREEN + "=" * 80 + colorama.Style.RESET_ALL)

# Global dict to track active WebSocket connections by user_id
active_connections = {}


# ==================== HELPER FUNCTIONS ====================

def save_avatar(base64_data: str) -> str:
    """Save avatar from base64 and return URL"""
    try:
        if not base64_data or 'base64,' not in base64_data:
            return None
        
        # Create upload folder if not exists
        upload_folder = "uploads/avatars"
        os.makedirs(upload_folder, exist_ok=True)
        
        # Decode base64
        image_data = base64.b64decode(base64_data.split('base64,')[1])
        
        # Generate unique filename
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(upload_folder, filename)
        
        # Save file
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        # Return URL path
        return f"/{filepath}"
        
    except Exception as e:
        print(colorama.Fore.RED + f"[AVATAR] Error saving: {e}" + colorama.Style.RESET_ALL)
        return None


async def handle_user_registration(websocket, data, face_image_bytes, state):
    """Handle new user registration"""
    try:
        # Save avatar if provided
        avatar_url = None
        if data.get('avatar'):
            avatar_url = save_avatar(data['avatar'])
        
        # Register user with face recognition
        user_id = face_detector.register_new_user(
            username=data['username'],
            full_name=data['fullName'],
            image_bytes=face_image_bytes,
            gender=data.get('gender', 'other'),
            birth_year=data.get('birthYear'),
            age=data.get('age'),
            avatar_url=avatar_url
        )
        
        if user_id:
            # Get user data
            user = db.get_user_by_id(user_id)
            
            # Create first conversation
            conv_id = db.create_conversation(user_id, "New Chat")
            
            # Update state
            state['current_user'] = user['username']
            state['current_user_id'] = user['id']
            state['current_conversation_id'] = conv_id
            state['user_checked'] = True
            state['face_greeted'] = True  # ✅ IMPORTANT: Enable voice chat
            
            # Send success (with safe defaults for NULL fields)
            await websocket.send(json.dumps({
                'type': 'registration_success',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'gender': user.get('gender') or 'other',  # ✅ Safe default
                    'age': user.get('age') or 0,  # ✅ Safe default
                    'avatar_url': user.get('avatar_url')  # ✅ Can be None
                },
                'conversation_id': conv_id,
                'message': f"Welcome, {user['full_name']}! 🎉"
            }))
            
            print(colorama.Fore.GREEN + f"[USER] ✅ Registered: {user['username']}" + colorama.Style.RESET_ALL)
            
            # Send greeting to enable voice chat
            greeting = f"Welcome, {user['full_name']}! I'm Bridge, your AI assistant. How can I help you today?"
            await websocket.send(json.dumps({
                'type': 'greeting',
                'content': greeting,
                'user': user['username'],
                'emotion': 'happy'
            }))
            
            # TTS greeting
            loop = asyncio.get_running_loop()
            state['is_processing'] = True
            wav_bytes = await loop.run_in_executor(None, tts.generate_audio_bytes, greeting)
            if wav_bytes:
                await websocket.send(json.dumps({"type": "audio", "content": "audio_data"}))
                await websocket.send(wav_bytes)
                await asyncio.sleep(len(greeting) * 0.08 + 0.5)
            state['is_processing'] = False
        else:
            await websocket.send(json.dumps({
                'type': 'registration_failed',
                'message': 'Failed to register. Please try again.'
            }))
            
    except Exception as e:
        print(colorama.Fore.RED + f"[REGISTRATION ERROR] {e}" + colorama.Style.RESET_ALL)
        await websocket.send(json.dumps({
            'type': 'registration_failed',
            'message': str(e)
        }))


async def handle_user_login(websocket, user):
    """Handle user auto-login"""
    try:
        # Update last login
        db.update_last_login(user['id'])
        
        # Track user for reminders
        active_connections[user['id']] = websocket
        print(colorama.Fore.CYAN + f"[REMINDER] User #{user['id']} tracked for notifications" + colorama.Style.RESET_ALL)
        
        # Get conversations
        conversations = db.get_conversations(user['id'], limit=50)
        
        # Send login success (with safe defaults for NULL fields)
        await websocket.send(json.dumps({
            'type': 'user_logged_in',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'gender': user.get('gender') or 'other',  # ✅ Default to 'other' if NULL
                'age': user.get('age') or 0,  # ✅ Default to 0 if NULL
                'avatar_url': user.get('avatar_url')  # ✅ Can be None
            },
            'conversations': [
                {
                    'id': c['id'],
                    'title': c['title'],
                    'updated_at': c['updated_at'].isoformat() if hasattr(c['updated_at'], 'isoformat') else str(c['updated_at'])
                }
                for c in conversations
            ]
        }))
        
        print(colorama.Fore.GREEN + f"[USER] ✅ Logged in: {user['username']}" + colorama.Style.RESET_ALL)
        
        # Check for missed reminders
        missed_reminders = db.get_missed_reminders(user['id'])
        if missed_reminders:
            print(colorama.Fore.YELLOW + f"[REMINDER] Found {len(missed_reminders)} missed reminder(s) for user #{user['id']}" + colorama.Style.RESET_ALL)
            
            # Send all missed reminders
            for reminder in missed_reminders:
                message = f"You missed this reminder: {reminder['title']}"
                if reminder['description']:
                    message += f". {reminder['description']}"
                
                await websocket.send(json.dumps({
                    'type': 'reminder_notification',
                    'reminder': {
                        'id': reminder['id'],
                        'title': reminder['title'],
                        'description': reminder['description']
                    },
                    'message': message,
                    'is_missed': True
                }))
                
                print(colorama.Fore.GREEN + f"[REMINDER] ✅ Sent missed reminder: {reminder['title']}" + colorama.Style.RESET_ALL)
        
    except Exception as e:
        print(colorama.Fore.RED + f"[LOGIN ERROR] {e}" + colorama.Style.RESET_ALL)


# ==================== WEBSOCKET HANDLERS ====================

async def handle_face_recognition(websocket, state, image_queue):
    """Task riêng xử lý face recognition từ video frames - CHECK USER + EMOTION"""
    loop = asyncio.get_running_loop()
    
    # Throttling: Chỉ xử lý 1 frame mỗi 0.5 giây
    last_process_time = 0
    PROCESS_INTERVAL = 0.5  # giây
    
    try:
        while True:
            # Lấy image từ queue
            image_data = await image_queue.get()
            
            if image_data is None:
                break
            
            # Throttling - Skip frames nếu xử lý quá nhanh
            current_time = time.time()
            if current_time - last_process_time < PROCESS_INTERVAL:
                continue  # Skip frame này
            
            last_process_time = current_time
            print(f"[FACE] Processing image: {len(image_data)} bytes")
            
            # ========== CHECK USER LẦN ĐẦU ==========
            if not state.get('user_checked'):
                # Analyze frame (recognize user + emotion)
                result = await loop.run_in_executor(
                    None,
                    face_detector.analyze_frame,
                    image_data
                )
                
                user = result.get('user')
                is_new_user = result.get('is_new_user', False)
                detected_emotion = result.get('emotion')
                greeting = result.get('greeting')
                
                if is_new_user:
                    # New user detected - show registration form
                    # Keep sending until frontend acknowledges (don't set user_checked yet)
                    if not state.get('registration_prompt_sent'):
                        print(colorama.Fore.YELLOW + "[FACE] ⚠️ New user detected - showing registration form" + colorama.Style.RESET_ALL)
                        state['registration_prompt_sent'] = True
                    
                    try:
                        await websocket.send(json.dumps({
                            'type': 'show_registration',
                            'message': 'Welcome! Please register to continue.'
                        }))
                        # Don't set user_checked = True yet, keep trying
                        # Will be set after successful registration
                    except websockets.exceptions.ConnectionClosed:
                        break
                elif user:
                    # Existing user - IMMEDIATELY hide registration form
                    print(colorama.Fore.GREEN + f"[FACE] User recognized: {user['username']}" + colorama.Style.RESET_ALL)
                    state['current_user'] = user['username']
                    state['current_user_id'] = user['id']
                    state['user_checked'] = True
                    state['is_new_user'] = False
                    state['registration_prompt_sent'] = False  # Reset flag
                    
                    try:
                        # FIRST: Hide registration form immediately
                        await websocket.send(json.dumps({
                            'type': 'hide_registration'
                        }))
                        
                        # THEN: Auto login
                        await handle_user_login(websocket, user)
                        
                        # Send greeting
                        if greeting:
                            await websocket.send(json.dumps({
                                'type': 'greeting',
                                'content': greeting,
                                'user': user['username'],
                                'emotion': detected_emotion
                            }))
                            state['face_greeted'] = True
                            
                            # TTS greeting
                            state['is_processing'] = True
                            wav_bytes = await loop.run_in_executor(None, tts.generate_audio_bytes, greeting)
                            if wav_bytes:
                                await websocket.send(json.dumps({"type": "audio", "content": "audio_data"}))
                                await websocket.send(wav_bytes)
                                await asyncio.sleep(len(greeting) * 0.08 + 0.5)
                            state['is_processing'] = False
                    except websockets.exceptions.ConnectionClosed:
                        print(colorama.Fore.YELLOW + "[FACE] WebSocket closed during login" + colorama.Style.RESET_ALL)
                        state['is_processing'] = False
                        break
            
            # ========== EMOTION UPDATES (sau khi đã login) ==========
            else:
                try:
                    detected_emotion = await loop.run_in_executor(
                        None,
                        face_detector.detect_emotion,
                        image_data
                    )
                    
                    # Cập nhật emotion vào state
                    if detected_emotion:
                        state['face_emotion'] = detected_emotion
                        
                        # Gửi emotion update
                        try:
                            await websocket.send(json.dumps({
                                "type": "emotion_update",
                                "emotion": detected_emotion,
                                "user": state.get('current_user', 'Unknown')
                            }))
                        except websockets.exceptions.ConnectionClosed:
                            print(colorama.Fore.YELLOW + "[FACE] WebSocket closed, stopping..." + colorama.Style.RESET_ALL)
                            break
                except Exception as e:
                    print(colorama.Fore.YELLOW + f"[FACE] Emotion detection error: {e}" + colorama.Style.RESET_ALL)
    
    except websockets.exceptions.ConnectionClosed:
        print(colorama.Fore.YELLOW + "[FACE] Client disconnected" + colorama.Style.RESET_ALL)
    except Exception as e:
        if "ConnectionClosed" not in str(type(e).__name__):
            print(colorama.Fore.RED + f"[FACE] Error: {e}" + colorama.Style.RESET_ALL)
            traceback.print_exc()


async def handle_voice_chat(websocket, state):
    """Task riêng xử lý voice chat (VAD + STT + LLM + TTS)"""
    loop = asyncio.get_running_loop()
    
    status_text = "Đang chờ..."
    last_vol = 0
    
    try:
        while True:
            # CHỜ ĐẾN KHI ĐÃ CHÀO HỎI
            if not state.get('face_greeted'):
                await asyncio.sleep(0.5)
                continue
            
            # Nếu đang xử lý voice thì không nghe
            if state['is_processing']:
                await asyncio.sleep(0.1)
                continue
            
            # Bắt đầu nghe
            t_start_listen = time.time()
            status_text = "Đang nghe..."
            
            # Lấy chunk âm thanh để vẽ thanh mic
            if vad.stream and vad.stream.is_active():
                try:
                    data_chunk = vad.stream.read(vad.CHUNK, exception_on_overflow=False)
                    last_vol = np.abs(np.frombuffer(data_chunk, dtype=np.int16)).mean()
                except:
                    last_vol = 0
            
            # Vẽ thanh mic
            bar = '#' * int(last_vol / 50)
            print(f"\r[MIC] {bar[:20]:<20} | {status_text:<30}", end='', flush=True)
            
            # Gọi VAD để nghe
            audio_data = await loop.run_in_executor(None, vad.listen)
            
            if audio_data is None:
                await asyncio.sleep(0.01)
                continue
            
            # Kiểm tra độ dài audio (tối thiểu ~0.5 giây ở 16kHz, 16-bit)
            min_audio_bytes = 16000  # ~0.5 giây
            if len(audio_data) < min_audio_bytes:
                print(colorama.Fore.YELLOW + f"[VAD] Audio quá ngắn: {len(audio_data)} bytes, bỏ qua..." + colorama.Style.RESET_ALL)
                continue
            
            # Log thông tin audio nhận được
            duration_seconds = len(audio_data) / (16000 * 2)  # 16kHz, 16-bit = 2 bytes/sample
            print(colorama.Fore.CYAN + f"\n[VAD] ✅ Đã ngắt câu. Audio: {len(audio_data)} bytes (~{duration_seconds:.2f}s)" + colorama.Style.RESET_ALL)
            
            # Bắt đầu xử lý
            state['is_processing'] = True
            t_vad_end = time.time()
            
            try:
                # 1. STT (Deepgram)
                status_text = "Đang nhận dạng giọng nói (Deepgram)..."
                t_stt_end = 0; t_llm_end = 0; t_tts_end = 0
                
                print(colorama.Fore.CYAN + f"[STT] Đang gửi {len(audio_data)} bytes đến Deepgram API..." + colorama.Style.RESET_ALL)
                text = await loop.run_in_executor(None, stt.recognize_audio, audio_data)
                t_stt_end = time.time()
                
                if not text:
                    print(colorama.Fore.YELLOW + "[STT] ⚠️ Không nhận dạng được text từ audio." + colorama.Style.RESET_ALL)
                    state['is_processing'] = False
                    status_text = "Đang chờ..."
                    continue
                
                # Phát hiện voice emotion
                voice_emotion = await loop.run_in_executor(None, voice_detector.detect_emotion, audio_data)
                if voice_emotion:
                    state['voice_emotion'] = voice_emotion
                    print(colorama.Fore.YELLOW + f"[VOICE EMOTION] {voice_emotion}" + colorama.Style.RESET_ALL)
                
                # Get face emotion from state
                face_emotion = state.get('face_emotion')
                combined_emotion = voice_emotion or face_emotion  # Ưu tiên voice emotion
                
                # ========== NEW: SAVE USER MESSAGE ==========
                conversation_id = state.get('current_conversation_id')
                if conversation_id:
                    db.add_message(
                        conversation_id=conversation_id,
                        role='user',
                        content=text,
                        user_emotion=combined_emotion
                    )
                
                # Log User input
                print("\n" + "=" * 80)
                print(colorama.Fore.BLUE + f"👤 USER: {text}" + colorama.Style.RESET_ALL)
                
                # Hiển thị emotion context
                user_name = state.get('current_user')
                
                if user_name or combined_emotion:
                    emotion_info = []
                    if user_name:
                        emotion_info.append(f"Name: {user_name}")
                    if combined_emotion:
                        emotion_info.append(f"Emotion: {combined_emotion}")
                    print(colorama.Fore.CYAN + f"[CONTEXT] {' | '.join(emotion_info)}" + colorama.Style.RESET_ALL)
                
                print("=" * 80)
                await websocket.send(json.dumps({"type": "log", "content": f"User: {text}"}))
                
                # TỐI ƯU: Gửi text về frontend ngay để user thấy
                await websocket.send(json.dumps({
                    "type": "user_text",
                    "content": text
                }))
                
                # 2. LLM (Cloudflare Workers AI - Llama 3.1)
                status_text = "AI đang suy nghĩ (Cloudflare)..."
                
                # TẮT MIC NGAY KHI BẮT ĐẦU XỬ LÝ LLM (để tránh feedback)
                vad.mute()
                
                response = await loop.run_in_executor(
                    None, 
                    llm.chat, 
                    text,
                    None,  # style (auto-detect)
                    combined_emotion,  # user_emotion
                    user_name  # user_name
                )
                t_llm_end = time.time()
                
                # ========== NEW: SAVE ASSISTANT MESSAGE ==========
                if conversation_id:
                    db.add_message(
                        conversation_id=conversation_id,
                        role='assistant',
                        content=response
                    )
                    
                    # ========== AUTO-GENERATE TITLE AFTER 3 MESSAGES ==========
                    messages = db.get_messages(conversation_id)
                    
                    # Only generate title once when we have 3+ messages and title is still "New Chat"
                    if len(messages) >= 3:
                        # Check if title is still default
                        conversations = db.get_conversations(state.get('current_user_id'), limit=1)
                        current_conv = next((c for c in conversations if c['id'] == conversation_id), None)
                        
                        if current_conv and current_conv['title'] == 'New Chat':
                            print(colorama.Fore.CYAN + "[TITLE] Generating conversation title..." + colorama.Style.RESET_ALL)
                            
                            # Format messages for title generation (use first 4 messages)
                            message_list = [
                                {"role": msg['role'], "content": msg['content']}
                                for msg in messages[:4]
                            ]
                            
                            # Generate title
                            title = await loop.run_in_executor(
                                None,
                                llm.generate_conversation_title,
                                message_list
                            )
                            
                            # Update conversation title
                            if title and title != "New Chat":
                                db.update_conversation_title(conversation_id, title)
                                print(colorama.Fore.GREEN + f"[TITLE] ✅ Updated: {title}" + colorama.Style.RESET_ALL)
                                
                                # Notify frontend to refresh conversations
                                try:
                                    await websocket.send(json.dumps({
                                        'type': 'title_updated',
                                        'conversation_id': conversation_id,
                                        'title': title
                                    }))
                                except:
                                    pass
                                pass
                
                # Log AI response
                print("\n" + colorama.Fore.MAGENTA + f"🤖 BRIDGE: {response}" + colorama.Style.RESET_ALL)
                print("=" * 80 + "\n")
                await websocket.send(json.dumps({"type": "log", "content": f"Bridge: {response}"}))
                
                # Gửi text response ngay lập tức
                await websocket.send(json.dumps({
                    "type": "text",
                    "content": response
                }))
                
                # 3. TTS (ElevenLabs) - Đã mute mic từ trước
                status_text = "Đang tạo giọng nói (ElevenLabs)..."
                clean_response = response.strip().replace("\n", " ").replace("\r", "")
                
                if not clean_response:
                    print(colorama.Fore.YELLOW + "[TTS] Response rỗng." + colorama.Style.RESET_ALL)
                    state['is_processing'] = False
                    status_text = "Đang chờ..."
                    vad.unmute()  # Nhớ unmute nếu response rỗng
                    continue
                
                # Mic đã được mute từ trước (khi bắt đầu LLM)
                
                wav_bytes = await loop.run_in_executor(None, tts.generate_audio_bytes, clean_response)
                t_tts_end = time.time()
                
                if wav_bytes:
                    # Tính thời gian
                    stt_time = t_stt_end - t_vad_end
                    llm_time = t_llm_end - t_stt_end
                    tts_time = t_tts_end - t_llm_end
                    total_time = t_tts_end - t_vad_end
                    
                    print(
                        f"\r[HOÀN THÀNH] STT:{stt_time:.2f}s | LLM:{llm_time:.2f}s | TTS:{tts_time:.2f}s | Tổng:{total_time:.2f}s",
                        end='', flush=True
                    )
                    print()
                    
                    # Gửi audio response
                    await websocket.send(json.dumps({
                        "type": "audio",
                        "content": "audio_data"
                    }))
                    await websocket.send(wav_bytes)
                    
                    # Ước lượng thời gian phát audio
                    # Turbo model: ~0.05s/ký tự
                    estimated_duration = len(clean_response) * 0.05
                    
                    # Đợi audio phát xong
                    await asyncio.sleep(estimated_duration)
                    
                    # MỞ LẠI MIC SAU KHI PHÁT XONG
                    vad.unmute()
                else:
                    print(colorama.Fore.RED + "[TTS] Không tạo được âm thanh." + colorama.Style.RESET_ALL)
                    # Vẫn phải unmute nếu TTS fail
                    vad.unmute()
            
            except Exception as e:
                print(colorama.Fore.RED + f"\n[LỖI XỬ LÝ] {e}" + colorama.Style.RESET_ALL)
                traceback.print_exc()
                # Đảm bảo unmute ngay cả khi có lỗi
                vad.unmute()
            
            # Kết thúc xử lý
            state['is_processing'] = False
            status_text = "Đang chờ..."
            print(colorama.Fore.GREEN + "[SYSTEM] ✅ Sẵn sàng nghe tiếp." + colorama.Style.RESET_ALL)
    
    except websockets.exceptions.ConnectionClosed:
        print(colorama.Fore.RED + "\n[WebSocket] Client disconnected" + colorama.Style.RESET_ALL)
    except Exception as e:
        print(colorama.Fore.RED + f"\n[SERVER LỖI] {e}" + colorama.Style.RESET_ALL)
        traceback.print_exc()


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
                            await handle_user_registration(websocket, data, last_face_image, state)
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
                    
                    # ========== NEW: CREATE NEW CONVERSATION ==========
                    elif cmd_type == 'create_conversation':
                        user_id = state.get('current_user_id')
                        if user_id:
                            # Create new conversation
                            conv_id = db.create_conversation(user_id, "New Chat")
                            state['current_conversation_id'] = conv_id
                            
                            # Send success and refresh conversations
                            await websocket.send(json.dumps({
                                'type': 'conversation_created',
                                'conversation_id': conv_id
                            }))
                            
                            # Send updated conversations list
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
                            
                            print(colorama.Fore.GREEN + f"[CONV] Created new conversation #{conv_id}" + colorama.Style.RESET_ALL)
                    
                    # ========== NEW: RESET GREETING STATE ==========
                    elif cmd_type == 'reset_greeting':
                        # Reset greeting state to allow new greeting
                        state['face_greeted'] = False
                        print(colorama.Fore.YELLOW + "[STATE] Greeting state reset - voice chat paused" + colorama.Style.RESET_ALL)
                        
                        # Send greeting for new conversation
                        user_name = state.get('current_user')
                        if user_name:
                            greeting = f"Ready for a new chat, {user_name}! What's on your mind?"
                            
                            await websocket.send(json.dumps({
                                'type': 'greeting',
                                'content': greeting,
                                'user': user_name
                            }))
                            
                            # TTS greeting
                            loop = asyncio.get_running_loop()
                            state['is_processing'] = True
                            wav_bytes = await loop.run_in_executor(None, tts.generate_audio_bytes, greeting)
                            if wav_bytes:
                                await websocket.send(json.dumps({"type": "audio", "content": "audio_data"}))
                                await websocket.send(wav_bytes)
                                await asyncio.sleep(len(greeting) * 0.08 + 0.5)
                            state['is_processing'] = False
                            state['face_greeted'] = True
                    
                    # ========== NEW: GET MESSAGES ==========
                    elif cmd_type == 'get_messages':
                        conv_id = data.get('conversation_id')
                        if conv_id:
                            messages = db.get_messages(conv_id)
                            await websocket.send(json.dumps({
                                'type': 'messages',
                                'messages': [
                                    {
                                        'role': m['role'],
                                        'content': m['content'],
                                        'timestamp': m['created_at'].isoformat() if hasattr(m['created_at'], 'isoformat') else str(m['created_at'])
                                    }
                                    for m in messages
                                ]
                            }))
                            state['current_conversation_id'] = conv_id
                    
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
                    
                    # ========== REMINDER MANAGEMENT ==========
                    elif cmd_type == 'create_reminder':
                        user_id = state.get('current_user_id')
                        if user_id:
                            title = data.get('title')
                            description = data.get('description', '')
                            reminder_time = data.get('reminder_time')
                            
                            reminder_id = db.create_reminder(user_id, title, reminder_time, description)
                            
                            if reminder_id:
                                await websocket.send(json.dumps({
                                    'type': 'reminder_created',
                                    'reminder_id': reminder_id
                                }))
                                
                                # Send updated reminders list
                                reminders = db.get_reminders(user_id)
                                await websocket.send(json.dumps({
                                    'type': 'reminders',
                                    'reminders': [
                                        {
                                            'id': r['id'],
                                            'title': r['title'],
                                            'description': r['description'],
                                            'reminder_time': r['reminder_time'].isoformat() if hasattr(r['reminder_time'], 'isoformat') else str(r['reminder_time']),
                                            'is_completed': r['is_completed']
                                        }
                                        for r in reminders
                                    ]
                                }))
                    
                    elif cmd_type == 'get_reminders':
                        user_id = state.get('current_user_id')
                        if user_id:
                            reminders = db.get_reminders(user_id)
                            await websocket.send(json.dumps({
                                'type': 'reminders',
                                'reminders': [
                                    {
                                        'id': r['id'],
                                        'title': r['title'],
                                        'description': r['description'],
                                        'reminder_time': r['reminder_time'].isoformat() if hasattr(r['reminder_time'], 'isoformat') else str(r['reminder_time']),
                                        'is_completed': r['is_completed']
                                    }
                                    for r in reminders
                                ]
                            }))
                    
                    elif cmd_type == 'complete_reminder':
                        reminder_id = data.get('reminder_id')
                        if reminder_id:
                            db.complete_reminder(reminder_id)
                            await websocket.send(json.dumps({
                                'type': 'reminder_completed',
                                'reminder_id': reminder_id
                            }))
                    
                    elif cmd_type == 'delete_reminder':
                        reminder_id = data.get('reminder_id')
                        if reminder_id:
                            db.delete_reminder(reminder_id)
                            await websocket.send(json.dumps({
                                'type': 'reminder_deleted',
                                'reminder_id': reminder_id
                            }))
                    
                    # ========== TITLE GENERATION ==========
                    elif cmd_type == 'generate_title':
                        conv_id = data.get('conversation_id')
                        if conv_id:
                            messages = db.get_messages(conv_id)
                            if len(messages) >= 2:
                                message_list = [
                                    {"role": msg['role'], "content": msg['content']}
                                    for msg in messages[:4]
                                ]
                                
                                loop = asyncio.get_running_loop()
                                title = await loop.run_in_executor(
                                    None,
                                    llm.generate_conversation_title,
                                    message_list
                                )
                                
                                if title and title != "New Chat":
                                    db.update_conversation_title(conv_id, title)
                                    await websocket.send(json.dumps({
                                        'type': 'title_updated',
                                        'conversation_id': conv_id,
                                        'title': title
                                    }))
                                    print(colorama.Fore.GREEN + f"[TITLE] Generated: {title}" + colorama.Style.RESET_ALL)
                    
                    # ========== MIC CONTROL ==========
                    elif cmd_type == 'mute_mic':
                        vad.mute()
                        print(colorama.Fore.YELLOW + "[MIC] 🔇 Muted by user" + colorama.Style.RESET_ALL)
                    
                    elif cmd_type == 'unmute_mic':
                        vad.unmute()
                        print(colorama.Fore.GREEN + "[MIC] 🔊 Unmuted by user" + colorama.Style.RESET_ALL)
                            
                except json.JSONDecodeError:
                    pass
            
            # 2. Xử lý image frames (bytes lớn hơn 5KB)
            elif isinstance(message, bytes) and len(message) > 5000:
                # Store for potential registration
                last_face_image = message
                
                # Đẩy vào queue để face_recognition xử lý
                await image_queue.put(message)
                
    except websockets.exceptions.ConnectionClosed:
        print(colorama.Fore.YELLOW + "[WS] Connection closed" + colorama.Style.RESET_ALL)
    except Exception as e:
        print(colorama.Fore.RED + f"[WS] Error: {e}" + colorama.Style.RESET_ALL)
        traceback.print_exc()
    finally:
        # Signal face recognition to stop
        await image_queue.put(None)


# ==================== REMINDER CALLBACK ====================

async def reminder_callback(reminder):
    """Callback when reminder is due - send notification via WebSocket"""
    user_id = reminder['user_id']
    
    print(colorama.Fore.CYAN + f"[REMINDER] Callback triggered for user #{user_id}: {reminder['title']}" + colorama.Style.RESET_ALL)
    
    # Mark as notified immediately (so it won't trigger again)
    db.mark_reminder_notified(reminder['id'])
    
    # Check if user is connected
    if user_id in active_connections:
        websocket = active_connections[user_id]
        print(colorama.Fore.GREEN + f"[REMINDER] User #{user_id} is ONLINE, sending notification..." + colorama.Style.RESET_ALL)
        
        try:
            # Send reminder notification
            message = f"Hey! It's time for: {reminder['title']}"
            if reminder['description']:
                message += f". {reminder['description']}"
            
            await websocket.send(json.dumps({
                'type': 'reminder_notification',
                'reminder': {
                    'id': reminder['id'],
                    'title': reminder['title'],
                    'description': reminder['description']
                },
                'message': message
            }))
            
            print(colorama.Fore.GREEN + f"[REMINDER] ✅ Notification sent to user #{user_id}" + colorama.Style.RESET_ALL)
            
            # Try to generate TTS (with fallback if rate limited)
            try:
                loop = asyncio.get_running_loop()
                wav_bytes = await loop.run_in_executor(None, tts.generate_audio_bytes, message)
                
                if wav_bytes:
                    await websocket.send(json.dumps({"type": "audio", "content": "audio_data"}))
                    await websocket.send(wav_bytes)
                    print(colorama.Fore.GREEN + f"[REMINDER] ✅ TTS sent to user #{user_id}" + colorama.Style.RESET_ALL)
                else:
                    print(colorama.Fore.YELLOW + f"[REMINDER] ⚠️ TTS unavailable" + colorama.Style.RESET_ALL)
            except Exception as tts_error:
                # TTS failed (rate limit or other error) - notification still sent
                print(colorama.Fore.YELLOW + f"[REMINDER] ⚠️ TTS failed: {tts_error}" + colorama.Style.RESET_ALL)
            
        except Exception as e:
            print(colorama.Fore.RED + f"[REMINDER] Error sending notification: {e}" + colorama.Style.RESET_ALL)
            import traceback
            traceback.print_exc()
    else:
        print(colorama.Fore.YELLOW + f"[REMINDER] User #{user_id} is OFFLINE, notification saved for later" + colorama.Style.RESET_ALL)


async def socket_handler(websocket):
    """Xử lý WebSocket connection - Điều phối giữa face recognition và voice chat"""
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
        'face_emotion': None,  # Cảm xúc từ khuôn mặt
        'voice_emotion': None,  # Cảm xúc từ giọng nói
        'register_mode': False,  # Chế độ đăng ký user mới
        'register_name': None  # Tên user đang đăng ký
    }
    
    # Queue để truyền image frames từ WebSocket đến face recognition
    image_queue = asyncio.Queue(maxsize=2)  # Giới hạn 2 frames để tránh lag
    
    try:
        # Chạy song song 3 tasks:
        # 1. Nhận WebSocket messages (video frames + commands)
        # 2. Xử lý face recognition
        # 3. Xử lý voice chat (VAD)
        await asyncio.gather(
            handle_websocket_messages(websocket, image_queue, state),
            handle_face_recognition(websocket, state, image_queue),
            handle_voice_chat(websocket, state),
            return_exceptions=True
        )
        
    except websockets.exceptions.ConnectionClosed:
        print(colorama.Fore.RED + "\n[WebSocket] Client disconnected" + colorama.Style.RESET_ALL)
    except Exception as e:
        print(colorama.Fore.RED + f"\n[SERVER LỖI] {e}" + colorama.Style.RESET_ALL)
        traceback.print_exc()
    finally:
        # Remove from active connections
        user_id = state.get('current_user_id')
        if user_id and user_id in active_connections:
            del active_connections[user_id]
            print(colorama.Fore.YELLOW + f"[REMINDER] User #{user_id} disconnected" + colorama.Style.RESET_ALL)


async def main():
    """Main server function"""
    print(colorama.Fore.CYAN + "\n[Server] Starting WebSocket Server on ws://localhost:8765..." + colorama.Style.RESET_ALL)
    
    # Set reminder callback
    reminder_scheduler.set_callback(reminder_callback)
    
    # Start scheduler in background
    scheduler_task = asyncio.create_task(reminder_scheduler.start())
    print(colorama.Fore.GREEN + "[REMINDER] Scheduler started in background" + colorama.Style.RESET_ALL)
    
    async with websockets.serve(socket_handler, "localhost", 8765):
        print(colorama.Fore.GREEN + "[Server] WebSocket Server is running. Press Ctrl+C to stop." + colorama.Style.RESET_ALL)
        print(colorama.Fore.CYAN + "📡 AI Reminder system active - checking every 30 seconds" + colorama.Style.RESET_ALL)
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(colorama.Fore.YELLOW + "\n\n👋 Server stopped" + colorama.Style.RESET_ALL)
        reminder_scheduler.stop()
    except KeyboardInterrupt:
        print(colorama.Fore.YELLOW + "\n[Server] Stopped by user." + colorama.Style.RESET_ALL)
