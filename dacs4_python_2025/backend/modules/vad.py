import pyaudio
import numpy as np
import torch
import time
import colorama
import collections  # Thư viện để dùng bộ đệm vòng (deque)


class VoiceDetector:
    def __init__(self):
        print(colorama.Fore.CYAN + "[VAD] Loading Silero VAD Model (Long Sentence Mode)..." + colorama.Style.RESET_ALL)
        # Tải model Silero VAD
        # Sử dụng onnx=True thường nhanh và ổn định hơn trên CPU
        try:
            self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                               model='silero_vad',
                                               trust_repo=True,
                                               onnx=True)
        except:
            # Fallback nếu không load được onnx
            self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                               model='silero_vad',
                                               trust_repo=True)

        self.audio = pyaudio.PyAudio()
        self.stream = None

        # Cấu hình Micro
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 512  # Kích thước mỗi khung hình (frame)

        # ======================================================================
        # CẤU HÌNH VAD CHO CÂU NÓI DÀI (QUAN TRỌNG NHẤT Ở ĐÂY)
        # ======================================================================
        self.SPEECH_THRESHOLD = 0.5  # Ngưỡng xác suất (0.5 là mức cân bằng)

        # 1. Tăng thời gian chờ im lặng:
        # Cho phép ngập ngừng lên tới 1.5 giây giữa câu mà không bị cắt.
        self.SILENCE_DURATION = 1.5

        # 2. Tăng thời gian nói tối đa:
        # Cho phép nói liên tục lên tới 30 giây.
        self.MAX_SPEECH_DURATION = 30.0

        self.PRE_BUFFER_DURATION = 0.5  # Giữ nguyên bộ đệm trước 0.5s để không mất âm đầu
        # ======================================================================

        # Tính toán số lượng frame cho bộ đệm trước
        self.pre_buffer_frames = int((self.RATE * self.PRE_BUFFER_DURATION) / self.CHUNK)

        # Index của Microphone ưu tiên (Thay đổi nếu cần)
        self.PREFERRED_MIC_INDEX = 1
        self.is_muted = False  # Thêm flag để kiểm soát mute/unmute
        self._init_stream()

    def _init_stream(self):
        if self.stream:
            try:
                self.stream.close()
            except:
                pass
        try:
            # Thử mở mic ID ưu tiên
            self.stream = self.audio.open(format=self.FORMAT,
                                          channels=self.CHANNELS,
                                          rate=self.RATE,
                                          input=True,
                                          input_device_index=self.PREFERRED_MIC_INDEX,
                                          frames_per_buffer=self.CHUNK)
            print(
                colorama.Fore.GREEN + f"[VAD] ✅ Đã kết nối Micro ID {self.PREFERRED_MIC_INDEX}" + colorama.Style.RESET_ALL)
            return True
        except:
            # Fallback mic mặc định
            print(
                colorama.Fore.YELLOW + f"[VAD] Không mở được Mic ID {self.PREFERRED_MIC_INDEX}, chuyển sang mic mặc định hệ thống." + colorama.Style.RESET_ALL)
            try:
                self.stream = self.audio.open(format=self.FORMAT,
                                              channels=self.CHANNELS,
                                              rate=self.RATE,
                                              input=True,
                                              frames_per_buffer=self.CHUNK)
                print(colorama.Fore.GREEN + "[VAD] ✅ Đã kết nối Micro mặc định." + colorama.Style.RESET_ALL)
                return True
            except Exception as e:
                print(
                    colorama.Fore.RED + f"[VAD Lỗi Init] Không thể mở bất kỳ Micro nào: {e}" + colorama.Style.RESET_ALL)
                return False

    def mute(self):
        """Tắt mic (dừng stream tạm thời)"""
        self.is_muted = True
        if self.stream and self.stream.is_active():
            self.stream.stop_stream()
            print(colorama.Fore.YELLOW + "[VAD] 🔇 Mic MUTED" + colorama.Style.RESET_ALL)
    
    def unmute(self):
        """Mở lại mic"""
        self.is_muted = False
        if self.stream and not self.stream.is_active():
            self.stream.start_stream()
            print(colorama.Fore.GREEN + "[VAD] 🔊 Mic UNMUTED" + colorama.Style.RESET_ALL)

    def listen(self):
        # Nếu mic đang bị mute, không nghe
        if self.is_muted:
            time.sleep(0.1)
            return None
        
        # frames: Danh sách chứa dữ liệu âm thanh chính thức của câu nói
        frames = []
        # pre_buffer: Bộ đệm vòng để lưu âm thanh trước khi nói (tránh mất âm đầu)
        pre_buffer = collections.deque(maxlen=self.pre_buffer_frames)

        silence_start_time = None
        speech_start_time = None
        is_speaking = False

        # Kiểm tra và khởi tạo lại stream nếu cần
        if self.stream is None or not self.stream.is_active():
            if not self._init_stream():
                time.sleep(2)  # Chờ lâu hơn xíu trước khi thử lại
                return None

        while True:
            try:
                # Đọc dữ liệu từ micro
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)

                # Chuẩn bị dữ liệu cho model VAD (float32)
                audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0

                # Dự đoán xác suất giọng nói
                with torch.no_grad():
                    # Sử dụng model(tensor, rate) là cách gọi chuẩn cho Silero
                    prob = self.model(torch.from_numpy(audio_chunk), self.RATE).item()

                if prob > self.SPEECH_THRESHOLD:
                    # --- PHÁT HIỆN ĐANG NÓI ---
                    if not is_speaking:
                        # Bắt đầu một câu nói mới
                        is_speaking = True
                        speech_start_time = time.time()
                        # print(colorama.Fore.CYAN + "\n[VAD] >> Bắt đầu nói..." + colorama.Style.RESET_ALL)

                        # Thêm bộ đệm trước vào đầu danh sách frames
                        frames.extend(pre_buffer)
                        pre_buffer.clear()

                    # Reset thời gian tính im lặng vì đang nói
                    silence_start_time = None
                    # Lưu frame hiện tại
                    frames.append(data)

                else:
                    # --- PHÁT HIỆN IM LẶNG (HOẶC TIẾNG ỒN NHỎ) ---
                    if is_speaking:
                        # Đang trong trạng thái nói mà gặp im lặng
                        frames.append(data)  # Vẫn lưu khoảng lặng này vào câu

                        if silence_start_time is None:
                            silence_start_time = time.time()

                        # ĐIỀU KIỆN 1: Ngắt câu nếu im lặng đủ lâu (SILENCE_DURATION)
                        if time.time() - silence_start_time > self.SILENCE_DURATION:
                            # print(colorama.Fore.GREEN + f"[VAD] >> Đã ngắt câu (Im lặng > {self.SILENCE_DURATION}s)" + colorama.Style.RESET_ALL)
                            return b''.join(frames)
                    else:
                        # Chưa nói gì, chỉ là tiếng ồn nền -> Lưu vào bộ đệm trước
                        pre_buffer.append(data)

                # ĐIỀU KIỆN 2: Ngắt cưỡng ép nếu nói quá dài (MAX_SPEECH_DURATION)
                if is_speaking and speech_start_time and (time.time() - speech_start_time > self.MAX_SPEECH_DURATION):
                    print(
                        colorama.Fore.YELLOW + f"\n[VAD] >> Đã ngắt câu (Quá dài > {self.MAX_SPEECH_DURATION}s)" + colorama.Style.RESET_ALL)
                    return b''.join(frames)

            except IOError as e:
                # Lỗi thường gặp khi mic bị rút ra hoặc quá tải
                print(
                    colorama.Fore.YELLOW + f"\n[VAD Warning] Lỗi đọc Mic (IOError), đang thử lại..." + colorama.Style.RESET_ALL)
                self._init_stream()
                time.sleep(0.5)
                # Reset trạng thái để tránh lỗi logic
                frames = []
                pre_buffer.clear()
                is_speaking = False
            except Exception as e:
                print(colorama.Fore.RED + f"\n[VAD Critical Error] {e}" + colorama.Style.RESET_ALL)
                self._init_stream()
                time.sleep(1)
                return None