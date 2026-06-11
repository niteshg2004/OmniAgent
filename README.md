# OmniAgent

A production-ready multimodal agentic AI system that processes text, PDF, image, and audio inputs; detects intent; plans and executes tools autonomously; and returns text responses with full execution traces.

## Architecture

```
omniagent/
├── backend/          # FastAPI + Python 3.11
│   ├── app/
│   │   ├── api/      # HTTP routes
│   │   ├── planner/  # Intent, plan, execute
│   │   ├── services/ # Business logic
│   │   ├── tools/    # Pure tool implementations
│   │   └── ...
│   ├── Dockerfile
│   └── ARCHITECTURE.md
├── frontend/         # Next.js + TypeScript + Tailwind
└── docker-compose.yml
```

## Quick Start (Local)

### Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add GROQ_API_KEY
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/upload` | Upload files (+ optional message) |
| POST | `/api/v1/agent` | Full agent pipeline (intent → plan → execute) |
| GET | `/docs` | Swagger UI |

### Agent example

```bash
curl -X POST http://localhost:8000/api/v1/agent \
  -F "message=Summarize this document" \
  -F "files=@report.pdf"
```

## Tools

| Tool | Description |
|------|-------------|
| `pdf_extractor` | Extract text from PDF |
| `image_ocr` | OCR on images |
| `audio_transcriber` | Transcribe audio (faster-whisper) |
| `youtube_transcript` | Fetch YouTube captions |
| `summarizer` | LLM summarization (Groq) |
| `sentiment_analyzer` | LLM sentiment analysis |
| `code_analyzer` | LLM code analysis |

## Docker

```bash
# Copy and configure environment
cp backend/.env.example backend/.env

docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## Render Deployment

Use `render.yaml` at the repo root. Set `GROQ_API_KEY` in the Render dashboard.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Yes (for LLM tools) | Groq API key |
| `GROQ_MODEL` | No | Default: `llama-3.3-70b-versatile` |
| `MAX_UPLOAD_SIZE_MB` | No | Default: 25 |
| `CORS_ORIGINS` | No | Default: `*` |

## Testing

```bash
cd backend && pytest tests/ -v
```

## System Dependencies

- **Tesseract OCR** — `brew install tesseract` (macOS) or `apt install tesseract-ocr` (Linux)
- **ffmpeg** — required for audio transcription
