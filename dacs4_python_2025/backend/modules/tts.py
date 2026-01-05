from elevenlabs import ElevenLabs, VoiceSettings
import colorama
import os
import time


class TextToSpeech:
    def __init__(self):
        print(colorama.Fore.CYAN + "[TTS] Connecting to ElevenLabs..." + colorama.Style.RESET_ALL)
        try:
            api_key = os.getenv("ELEVENLABS_API_KEY", "")
            voice_id = os.getenv("ELEVENLABS_VOICE_ID", "")
            if not api_key:
                raise ValueError("Missing ELEVENLABS_API_KEY in .env")
            self.client = ElevenLabs(api_key=api_key)
            self.voice_id = voice_id
            
            # TỐI ƯU: Giảm stability để tăng tốc độ
            # Stability thấp = nhanh hơn nhưng ít ổn định hơn
            self.voice_settings = VoiceSettings(
                stability=0.3,  # Giảm từ 0.5 xuống 0.3
                similarity_boost=0.75,  # Giảm từ 0.85 xuống 0.75
                style=0.0, 
                use_speaker_boost=True
            )
            
            # TỐI ƯU: Dùng model turbo v2.5 (nhanh hơn 2x)
            self.model_id = "eleven_turbo_v2_5"  # Thay vì "eleven_multilingual_v2"
            
            print(colorama.Fore.GREEN + "[TTS] ✅ Connected! Using Turbo V2.5 model" + colorama.Style.RESET_ALL)
        except Exception as e:
            print(colorama.Fore.RED + f"[TTS ERROR] {e}" + colorama.Style.RESET_ALL)
            exit(1)
    
    def generate_audio_bytes(self, text):
        if not text or len(text.strip()) < 2:
            return None
        try:
            start_time = time.time()
            print(f"[TTS] Generating audio for {len(text)} chars...")
            
            # TỐI ƯU: Thêm optimize_streaming_latency
            audio_generator = self.client.text_to_speech.convert(
                voice_id=self.voice_id, 
                text=text, 
                model_id=self.model_id, 
                voice_settings=self.voice_settings,
                optimize_streaming_latency=4  # 0-4, 4 = fastest
            )
            
            audio_bytes = b"".join(audio_generator)
            
            if audio_bytes:
                duration = time.time() - start_time
                print(colorama.Fore.GREEN + f"[TTS] ✅ Success in {duration:.2f}s ({len(audio_bytes)} bytes)" + colorama.Style.RESET_ALL)
                return audio_bytes
            return None
        except Exception as e:
            print(colorama.Fore.RED + f"[TTS ERROR] {e}" + colorama.Style.RESET_ALL)
            return None
