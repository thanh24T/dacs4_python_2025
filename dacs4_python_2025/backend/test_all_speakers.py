"""
Test tất cả các giọng nói của Valtec TTS
So sánh chất lượng giữa các speaker
"""

import colorama
from modules.tts_valtec import TextToSpeech
import time

colorama.init()

def test_all_speakers():
    """Test tất cả các giọng nói"""
    
    # Câu test
    test_text = "Xin chào, tôi là trợ lý AI của bạn. Hôm nay thời tiết thật đẹp."
    
    # Danh sách speakers
    speakers = ["NF", "SF", "NM1", "SM", "NM2"]
    
    print("="*80)
    print("TEST TẤT CẢ CÁC GIỌNG NÓI VALTEC TTS")
    print("="*80)
    print(f"\nCâu test: {test_text}\n")
    
    for speaker in speakers:
        print(f"\n{'='*80}")
        print(f"🎤 SPEAKER: {speaker}")
        print(f"{'='*80}")
        
        try:
            # Khởi tạo TTS với speaker này
            tts = TextToSpeech(speaker=speaker, device="cpu")
            
            # Tạo audio
            start_time = time.time()
            audio_bytes = tts.generate_audio_bytes(test_text)
            elapsed = time.time() - start_time
            
            if audio_bytes:
                # Lưu file
                output_file = f"test_speaker_{speaker}.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_bytes)
                
                print(colorama.Fore.GREEN + f"✅ Đã lưu: {output_file}" + colorama.Style.RESET_ALL)
                print(colorama.Fore.YELLOW + f"⏱️  Thời gian: {elapsed:.2f}s" + colorama.Style.RESET_ALL)
                print(colorama.Fore.YELLOW + f"📦 Kích thước: {len(audio_bytes):,} bytes" + colorama.Style.RESET_ALL)
            else:
                print(colorama.Fore.RED + "❌ Không tạo được audio" + colorama.Style.RESET_ALL)
                
        except Exception as e:
            print(colorama.Fore.RED + f"❌ Lỗi: {e}" + colorama.Style.RESET_ALL)
    
    print(f"\n{'='*80}")
    print("✅ HOÀN THÀNH! Hãy nghe các file WAV để so sánh chất lượng")
    print(f"{'='*80}\n")
    
    # Thông tin về các speaker
    print("\n📋 THÔNG TIN CÁC GIỌNG NÓI:")
    print("-" * 80)
    print("NF  : Nữ Bắc (Female Northern)")
    print("SF  : Nữ Nam (Female Southern)")
    print("NM1 : Nam Bắc 1 (Male Northern 1)")
    print("SM  : Nam Nam (Male Southern)")
    print("NM2 : Nam Bắc 2 (Male Northern 2)")
    print("-" * 80)


if __name__ == "__main__":
    test_all_speakers()
