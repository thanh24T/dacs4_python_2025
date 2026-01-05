"""
Speech to Text - Deepgram REST API
Dùng REST API trực tiếp thay vì SDK v5 (quá nhiều bug)
"""

import colorama
import io
import wave
import requests
import os
from pathlib import Path

class SpeechToText:
    def __init__(self):
        print(colorama.Fore.CYAN + "[STT] Đang kết nối tới Deepgram (REST API)..." + colorama.Style.RESET_ALL)
        
        # Ưu tiên lấy API key từ environment variables
        self.api_key = os.getenv('DEEPGRAM_API_KEY')
        
        # Fallback: Đọc từ file .env nếu không có trong environment
        if not self.api_key:
            env_path = Path(__file__).parent.parent / '.env'
            if env_path.exists():
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('DEEPGRAM_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                            break
        
        if not self.api_key:
            print(colorama.Fore.RED + "[STT] ❌ Chưa có DEEPGRAM_API_KEY!" + colorama.Style.RESET_ALL)
            print(colorama.Fore.YELLOW + "[STT] Vui lòng set biến môi trường DEEPGRAM_API_KEY hoặc thêm vào file backend/.env" + colorama.Style.RESET_ALL)
            raise ValueError("DEEPGRAM_API_KEY not found in environment or .env file")
        
        self.api_url = "https://api.deepgram.com/v1/listen"
        self.headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "audio/wav"
        }
        
        print(colorama.Fore.GREEN + "[STT] ✅ Kết nối thành công!" + colorama.Style.RESET_ALL)
    
    def recognize_audio(self, audio_data: bytes) -> str:
        """Nhận dạng giọng nói từ audio bytes"""
        
        # Kiểm tra đầu vào
        if audio_data is None:
            print(colorama.Fore.RED + "[STT ERROR] audio_data is None!" + colorama.Style.RESET_ALL)
            return ""
        
        if len(audio_data) == 0:
            print(colorama.Fore.RED + "[STT ERROR] audio_data is empty!" + colorama.Style.RESET_ALL)
            return ""
        
        # Bỏ qua nếu âm thanh quá ngắn (ít hơn ~0.8 giây ở 16kHz, 16-bit)
        min_bytes = 25600  # ~0.8 giây (giảm từ 1s xuống 0.8s)
        if len(audio_data) < min_bytes:
            print(colorama.Fore.YELLOW + f"[STT] Audio quá ngắn: {len(audio_data)} bytes (tối thiểu: {min_bytes} bytes)" + colorama.Style.RESET_ALL)
            return ""
        
        # Kiểm tra độ dài audio (tính bằng giây)
        duration_seconds = len(audio_data) / (16000 * 2)  # 16kHz, 16-bit = 2 bytes/sample
        print(colorama.Fore.CYAN + f"[STT] Nhận audio: {len(audio_data)} bytes (~{duration_seconds:.2f}s)" + colorama.Style.RESET_ALL)
        
        # Kiểm tra volume - nếu quá nhỏ thì bỏ qua
        import numpy as np
        audio_array = np.frombuffer(audio_data, dtype=np.int16)
        volume = np.abs(audio_array).mean()
        
        if volume < 50:  # ✅ LOWERED: Accept quieter audio (was 100)
            print(colorama.Fore.YELLOW + f"[STT] Volume quá thấp ({volume:.0f}), có thể là silence" + colorama.Style.RESET_ALL)
            return ""
        
        try:
            # Tạo WAV file trong memory
            wav_stream = io.BytesIO()
            with wave.open(wav_stream, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(audio_data)
            
            wav_stream.seek(0)
            wav_bytes = wav_stream.read()
            
            # Gọi Deepgram REST API
            params = {
                "model": "nova-2",
                "language": "en",  # Đổi sang tiếng Anh
                "smart_format": "true",
                "punctuate": "true",
                "diarize": "false",
                "utterances": "false"
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                params=params,
                data=wav_bytes,
                timeout=8  # Giảm từ 10s xuống 8s
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Parse response
                if result.get('results', {}).get('channels'):
                    channel = result['results']['channels'][0]
                    if channel.get('alternatives'):
                        text = channel['alternatives'][0]['transcript'].strip()
                        confidence = channel['alternatives'][0].get('confidence', 0)
                        
                        if text:
                            print(colorama.Fore.GREEN + f"[STT] ✅ Nhận dạng: '{text}' (confidence: {confidence:.2f})" + colorama.Style.RESET_ALL)
                            return text
                        else:
                            print(colorama.Fore.YELLOW + f"[STT] Transcript rỗng (confidence: {confidence:.2f}) - Có thể là silence hoặc noise" + colorama.Style.RESET_ALL)
                    else:
                        print(colorama.Fore.YELLOW + "[STT] Không có alternatives trong response" + colorama.Style.RESET_ALL)
                else:
                    print(colorama.Fore.YELLOW + "[STT] Không có channels trong response" + colorama.Style.RESET_ALL)
            else:
                error_text = response.text[:500] if hasattr(response, 'text') else str(response.content[:500])
                print(colorama.Fore.RED + f"[STT ERROR] API returned {response.status_code}: {error_text}" + colorama.Style.RESET_ALL)
            
            return ""
            
        except requests.exceptions.Timeout:
            print(colorama.Fore.RED + "[STT ERROR] Timeout khi gọi Deepgram API (quá 10 giây)" + colorama.Style.RESET_ALL)
            return ""
        except requests.exceptions.ConnectionError as e:
            print(colorama.Fore.RED + f"[STT ERROR] Lỗi kết nối đến Deepgram API: {e}" + colorama.Style.RESET_ALL)
            return ""
        except wave.Error as e:
            print(colorama.Fore.RED + f"[STT ERROR] Lỗi tạo WAV file: {e}" + colorama.Style.RESET_ALL)
            return ""
        except Exception as e:
            print(colorama.Fore.RED + f"[STT ERROR] Lỗi không xác định: {type(e).__name__}: {e}" + colorama.Style.RESET_ALL)
            import traceback
            traceback.print_exc()
            return ""
