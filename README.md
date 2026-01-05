

- 🎤 Voice chat with AI (Deepgram STT + Cloudflare LLM + Valtec TTS)
- 👤 Face recognition & emotion detection (ArcFace + DeepFace)
- 🔔 AI reminder system with notifications
- 💬 Chat history per user
- 🎨 Modern UI with React + TypeScript



### 1. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Setup database
python setup_database.py

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run server
python server_rag.py
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### 3. Access

Open http://localhost:5173 in your browser

## Environment Variables

Required in `backend/.env`:

```env
# Deepgram (STT)
DEEPGRAM_API_KEY=your_key

# Cloudflare (LLM)
CLOUDFLARE_ACCOUNT_ID=your_id
CLOUDFLARE_API_TOKEN=your_token

# MySQL
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=voice_chat_db
```

## Tech Stack

**Backend:**
- Python 3.10+
- FastAPI + WebSockets
- MySQL
- DeepFace (ArcFace model)
- Deepgram API
- Cloudflare Workers AI
- Valtec TTS

**Frontend:**
- React 18
- TypeScript
- Vite
- TailwindCSS

## Project Structure

```
dacs4_python_2025/
├── backend/
│   ├── modules/          # Core modules
│   ├── database/         # SQL schemas
│   ├── tools/            # Utility scripts
│   ├── server_rag.py     # Main server
│   └── setup_database.py # DB setup
├── frontend/
│   └── src/
│       ├── components/   # React components
│       └── App.tsx       # Main app
└── README.md
```

## License

MIT
