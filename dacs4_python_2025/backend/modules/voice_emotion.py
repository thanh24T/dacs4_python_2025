"""
Voice Emotion Detection Module
Phát hiện cảm xúc từ giọng nói (pitch, energy, tempo)
"""

import librosa
import numpy as np
import colorama
from typing import Optional
import io


class VoiceEmotionDetector:
    def __init__(self):
        print(colorama.Fore.CYAN + "[VOICE EMOTION] Initializing..." + colorama.Style.RESET_ALL)
        print(colorama.Fore.GREEN + "[VOICE EMOTION] ✅ Ready!" + colorama.Style.RESET_ALL)
    
    def detect_emotion(self, audio_data: bytes) -> Optional[str]:
        """
        Phát hiện cảm xúc từ audio
        
        Args:
            audio_data: Raw audio bytes (16-bit PCM, 16kHz)
        
        Returns:
            Emotion: 'happy', 'sad', 'angry', 'neutral', 'stressed'
        """
        try:
            # Load audio
            y, sr = librosa.load(io.BytesIO(audio_data), sr=16000)
            
            # Extract features
            pitch = librosa.yin(y, fmin=50, fmax=300).mean()
            energy = librosa.feature.rms(y=y).mean()
            tempo = librosa.beat.tempo(y=y, sr=sr)[0]
            
            # Simple rule-based classification
            # (In production, use ML model)
            
            # High pitch + high energy + fast tempo = Happy/Excited
            if pitch > 150 and energy > 0.05 and tempo > 120:
                emotion = 'happy'
            
            # Low pitch + low energy + slow tempo = Sad
            elif pitch < 120 and energy < 0.03 and tempo < 90:
                emotion = 'sad'
            
            # High energy + fast tempo = Angry
            elif energy > 0.06 and tempo > 130:
                emotion = 'angry'
            
            # Variable pitch + high energy = Stressed
            elif energy > 0.05:
                emotion = 'stressed'
            
            # Default
            else:
                emotion = 'neutral'
            
            print(colorama.Fore.CYAN + f"[VOICE EMOTION] {emotion} (pitch:{pitch:.1f}, energy:{energy:.3f}, tempo:{tempo:.1f})" + colorama.Style.RESET_ALL)
            return emotion
            
        except Exception as e:
            print(colorama.Fore.YELLOW + f"[VOICE EMOTION] Error: {e}" + colorama.Style.RESET_ALL)
            return None


# Test
if __name__ == "__main__":
    colorama.init()
    detector = VoiceEmotionDetector()
    print("✅ Voice Emotion Detector initialized!")
