# OmniAgent Architecture

## Overview

OmniAgent is a multimodal agentic AI system that accepts text and file uploads (PDF, image, audio), understands user intent, plans minimal tool execution, and returns text responses with a full execution trace.

The backend follows a **layered architecture** with strict separation of concerns:

```
Client (Next.js)
       │
       ▼
┌──────────────────────────────────────────────────────────┐
│  api/          HTTP layer — routes, request validation   │
├──────────────────────────────────────────────────────────┤
│  services/     Business logic — orchestration entrypoint │
├──────────────────────────────────────────────────────────┤
│  planner/      Intent detection, planning, execution     │
├──────────────────────────────────────────────────────────┤
│  tools/        Pure tool implementations (no HTTP/LLM)   │
├──────────────────────────────────────────────────────────┤
│  schemas/      Pydantic models — contracts between layers│
├──────────────────────────────────────────────────────────┤
│  core/         Config, logging, shared exceptions        │
├──────────────────────────────────────────────────────────┤
│  utils/        Stateless helpers (files, text, URLs)     │
└──────────────────────────────────────────────────────────┘
```

## Request Lifecycle

```
POST /api/v1/agent
  │
  ├─ 1. api/          Validate multipart request (text + files)
  │
  ├─ 2. services/     Persist uploads, build AgentContext
  │
  ├─ 3. planner/      Detect intent
  │       ├─ ambiguous? → return follow-up question (no tool execution)
  │       └─ clear intent → build minimal ExecutionPlan
  │
  ├─ 4. planner/      Execute plan step-by-step
  │       └─ each step calls tools/ via ToolRegistry
  │
  └─ 5. api/          Return AgentResponse { text, trace, follow_up? }
```

## Layer Responsibilities

### `api/`
- FastAPI routers only
- Input validation via Pydantic schemas
- HTTP status codes and error mapping
- No business logic

### `services/`
- Coordinates planner + file handling
- Single entry point: `AgentService.process_request()`
- Translates domain errors to API responses

### `planner/`
- **IntentDetector** — classifies user goal; returns `FollowUpQuestion` when ambiguous
- **Planner** — produces minimal ordered `PlanStep` list
- **Executor** — runs steps sequentially, accumulates `ExecutionTrace`

### `tools/`
- Pure functions/classes with no FastAPI or planner imports
- Each tool: single responsibility, typed inputs/outputs
- Registered in `ToolRegistry` for discovery by name

### `schemas/`
- Shared Pydantic v2 models
- API contracts, trace format, tool results

### `core/`
- `Settings` (pydantic-settings)
- Structured logging configuration
- Domain exception hierarchy

### `utils/`
- File type detection, temp file management, URL extraction
- No domain logic

## Tool Catalog (Planned)

| Tool | Module | Purpose |
|------|--------|---------|
| `pdf_extractor` | `pdf_tool.py` | Extract text from PDF via PyMuPDF |
| `image_ocr` | `image_tool.py` | OCR via Pillow + pytesseract |
| `audio_transcriber` | `audio_tool.py` | Transcribe via faster-whisper |
| `youtube_transcript` | `youtube_tool.py` | Fetch transcript via youtube-transcript-api |
| `summarizer` | `summary_tool.py` | LLM summarization |
| `sentiment_analyzer` | `sentiment_tool.py` | LLM sentiment analysis |
| `code_analyzer` | `code_tool.py` | Extract/analyze code blocks |

## Execution Trace Contract

Every agent request returns a trace array:

```json
[
  { "step": 1, "tool": "pdf_extractor", "status": "success" },
  { "step": 2, "tool": "youtube_transcript", "status": "success" },
  { "step": 3, "tool": "summarizer", "status": "failed", "error": "..." }
]
```

Rules:
- Steps are numbered sequentially starting at 1
- `status` is one of: `success`, `failed`, `skipped`
- Failed steps include `error`; execution continues when partial results are useful
- Every tool invocation is logged at INFO with step number and duration

## Data Flow Example

**User:** "Summarize the YouTube video mentioned in this PDF" + PDF file

```
Intent: summarize_youtube_from_pdf
Plan:
  1. pdf_extractor(file=uploaded_pdf)
  2. url_extractor(text=step1.output)        # utils, not a scored tool
  3. youtube_transcript(url=step2.output)
  4. summarizer(text=step3.output)

Trace: [pdf_extractor ✓, youtube_transcript ✓, summarizer ✓]
Response: "The video discusses..."
```

## Key Design Decisions

### 1. No agent frameworks
Plain Python orchestration. The planner uses the Groq API (via the official `groq` SDK) for intent detection and LLM-backed tools. This keeps the execution path inspectable and interview-friendly.

### 2. Tools are pure
Tools accept typed inputs and return `ToolResult`. They never call each other. The planner decides execution order. This makes unit testing trivial and traces deterministic.

### 3. Minimal plans
The planner generates the shortest valid tool chain. No speculative tool calls. URL detection is a utility step, not a user-visible tool unless required by the rubric.

### 4. Fail gracefully, return partials
If step 3 fails, steps 1–2 outputs are still available. The response explains what succeeded and what failed.

### 5. Ambiguity → ask, don't guess
Upload-only requests with no text return a follow-up question. The planner does not assume "summarize" or "extract".

### 6. `api/` not `routes/`
FastAPI convention and forward-compatibility for `/api/v1/`, `/api/v2/`.

## Tradeoffs

| Decision | Benefit | Cost |
|----------|---------|------|
| Sequential execution | Simple traces, easy debugging | Slower for independent tools |
| LLM for intent | Handles natural language | Latency + API cost per request |
| Temp files for uploads | Works with all libraries | Disk I/O; must clean up in `finally` |
| faster-whisper (local) | No API cost for audio | Large model download; CPU/GPU bound |
| Pydantic everywhere | Validation at boundaries | Boilerplate for simple payloads |
| No LangChain | Full control, readable code | Must implement retry/parsing ourselves |

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| PDF only, no message | Return follow-up: "What would you like me to do with the PDF?" |
| Corrupt PDF | `pdf_extractor` fails; trace shows error; partial response if other files succeeded |
| Image with no text | OCR returns empty string; downstream tools handle gracefully |
| YouTube video without captions | `youtube_transcript` fails with clear error |
| Multiple files + vague prompt | Intent detector asks which file to focus on |
| Audio > size limit | Reject at API layer with 413 |
| Missing `GROQ_API_KEY` | LLM tools fail fast with config error in trace |
| Tesseract not installed | `image_ocr` fails with install instructions |
| Mixed file types | Planner selects only required tools per intent |

## Testing Strategy

### Unit tests (`tests/unit/`)
- Each tool in isolation with fixture files
- Planner plan generation with mocked LLM responses
- Intent detector: ambiguous vs clear cases
- Schema validation edge cases

### Integration tests (`tests/integration/`)
- Full request → response via `TestClient`
- Multi-file upload scenarios
- Trace shape and ordering assertions

### Test fixtures (`tests/fixtures/`)
- Sample PDF, PNG, MP3, corrupt files
- Mock LLM responses for deterministic planner tests

### CI checks
- `pytest` with coverage on `app/`
- `mypy` or `pyright` for type checking
- `ruff` for linting

## Phase Roadmap

| Phase | Deliverable |
|-------|-------------|
| 1 | Folder structure + architecture (this document)  |
| 2 | FastAPI setup (main.py, middleware, health) |
| 3 | Upload endpoint (multipart, temp files) |
| 4 | PDF extraction tool  |
| 5 | Image OCR tool  |
| 6 | Audio transcription tool |
| 7 | Summarization tool  |
| 8 | Intent detection  |
| 9 | Planner + executor  |
| 10 | Execution trace system  |
| 11 | Next.js frontend |
| 12 | Docker + Render deployment |
