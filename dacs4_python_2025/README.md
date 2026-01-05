# 🎙️ AI Voice Chat Clone - RAG + Few-shot Learning

> Hệ thống Voice Chat AI với RAG, phản hồi nhanh gấp 5 lần

---

## 🚀 QUICK START

### 1. Cài dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Thêm API Key

Mở `backend/.env` và điền:
```env
GROQ_API_KEY=your_groq_api_key_here
```

Lấy key tại: https://console.groq.com (miễn phí)

### 3. Khởi tạo RAG (lần đầu)

```bash
cd backend
python -m modules.rag_system
```

### 4. Chạy

```bash
# Terminal 1: Backend
cd backend
python server_rag.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Truy cập: http://localhost:5173

---

## 📊 Hiệu năng

- STT: 0.3s (Groq Whisper)
- LLM: 0.5s (Groq + RAG)
- TTS: 1-2s (ElevenLabs)
- **Tổng: 2-3s** (nhanh hơn 5x)

---

## 🎭 2 Phong cách

- **Triết lý/Sâu sắc**: Response dài, thấu đáo
- **Bạn bè thân thiết**: Response ngắn, thoải mái

Tự động phát hiện và điều chỉnh dựa trên câu hỏi.

---

## 🧪 Test

```bash
cd backend
python test_rag.py      # Test hệ thống
python benchmark.py     # Test tốc độ STT→LLM→TTS
```

Benchmark sẽ đo:
- Thời gian STT (Speech-to-Text)
- Thời gian LLM (Language Model + RAG)
- Thời gian TTS (Text-to-Speech)
- So sánh với hệ thống cũ

---

## 📁 Cấu trúc

```
backend/
├── data/conversations/     # 853 conversations
├── modules/
│   ├── rag_system.py      # RAG Engine
│   ├── llm_groq.py        # Groq LLM
│   └── stt_groq.py        # Groq Whisper
├── server_rag.py          # Main server
└── .env                   # API keys
```

---

**Made with ❤️**
