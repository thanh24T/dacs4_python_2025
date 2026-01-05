"""
Test các tham số khác nhau của TTS để tìm cấu hình tốt nhất
"""

import colorama
from valtec_tts import TTS
import soundfile as sf
import io
import time

colorama.init()

def test_parameters():
    """Test các tham số khác nhau"""
    
    print("="*80)
    print("TEST CÁC THAM SỐ TTS")
    print("="*80)
    
    # Khởi tạo TTS
    print("\n[1] Đang khởi tạo TTS...")
    tts = TTS(device="cpu")
    
    # Câu test
    test_text = "Xin chào, tôi là trợ lý AI của bạn."
    speaker = "NF"
    
    # Các cấu hình để test
    configs = [
        {
            "name": "GitHub Default",
            "speed": 1.0,
            "noise_scale": 0.667,
            "noise_scale_w": 0.8,
            "sdp_ratio": 0.0
        },
        {
            "name": "Faster Speed",
            "speed": 0.9,
            "noise_scale": 0.667,
            "noise_scale_w": 0.8,
            "sdp_ratio": 0.0
        },
        {
            "name": "Lower Noise",
            "speed": 1.0,
            "noise_scale": 0.5,
            "noise_scale_w": 0.6,
            "sdp_ratio": 0.0
        },
        {
            "name": "Higher Noise",
            "speed": 1.0,
            "noise_scale": 0.8,
            "noise_scale_w": 1.0,
            "sdp_ratio": 0.0
        },
        {
            "name": "Stochastic",
            "speed": 1.0,
            "noise_scale": 0.667,
            "noise_scale_w": 0.8,
            "sdp_ratio": 0.5
        },
        {
            "name": "Full Random",
            "speed": 1.0,
            "noise_scale": 0.667,
            "noise_scale_w": 0.8,
            "sdp_ratio": 1.0
        }
    ]
    
    print(f"\n[2] Test với câu: '{test_text}'")
    print(f"[3] Speaker: {speaker}\n")
    
    for i, config in enumerate(configs, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {config['name']}")
        print(f"{'='*80}")
        print(f"  speed         : {config['speed']}")
        print(f"  noise_scale   : {config['noise_scale']}")
        print(f"  noise_scale_w : {config['noise_scale_w']}")
        print(f"  sdp_ratio     : {config['sdp_ratio']}")
        
        try:
            # Tạo audio
            start_time = time.time()
            audio, sr = tts.synthesize(
                text=test_text,
                speaker=speaker,
                speed=config['speed'],
                noise_scale=config['noise_scale'],
                noise_scale_w=config['noise_scale_w'],
                sdp_ratio=config['sdp_ratio']
            )
            elapsed = time.time() - start_time
            
            # Lưu file
            output_file = f"test_param_{i}_{config['name'].replace(' ', '_')}.wav"
            sf.write(output_file, audio, sr)
            
            print(colorama.Fore.GREEN + f"\n✅ Đã lưu: {output_file}" + colorama.Style.RESET_ALL)
            print(colorama.Fore.YELLOW + f"⏱️  Thời gian: {elapsed:.2f}s" + colorama.Style.RESET_ALL)
            print(colorama.Fore.YELLOW + f"📊 Độ dài audio: {len(audio)/sr:.2f}s" + colorama.Style.RESET_ALL)
            
        except Exception as e:
            print(colorama.Fore.RED + f"\n❌ Lỗi: {e}" + colorama.Style.RESET_ALL)
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*80}")
    print("✅ HOÀN THÀNH! Hãy nghe các file để so sánh")
    print(f"{'='*80}\n")
    
    print("\n📋 GIẢI THÍCH CÁC THAM SỐ:")
    print("-" * 80)
    print("speed         : Tốc độ nói (1.0 = bình thường, <1.0 = nhanh, >1.0 = chậm)")
    print("noise_scale   : Độ biến thiên giọng nói (càng cao càng đa dạng)")
    print("noise_scale_w : Độ biến thiên thời lượng âm tiết")
    print("sdp_ratio     : 0 = xác định (giống nhau mỗi lần), 1 = ngẫu nhiên")
    print("-" * 80)


if __name__ == "__main__":
    test_parameters()
