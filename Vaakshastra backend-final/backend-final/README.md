# VaakShastra

AI-powered legal assistant for Indian courts. Upload a case document and get a plain-language summary, key facts, applicable IPC sections, a verdict prediction with reasoning, and a list of similar past judgments — all through a clean REST API.

Built with FastAPI, SQLAlchemy (async SQLite), and the Groq LLM API.

## Features

- User signup, login, and profile via JWT authentication.
- Document upload for PDF and TXT files (max 10 MB) with automatic text extraction and word/page counting.
- AI analysis of a document or raw text, returning:
  - Plain-language summary
  - Key facts
  - Applicable IPC / legal sections
  - Verdict prediction with confidence score and reasoning
  - Similar past Indian court cases
- Multi-language output and configurable analysis depth (`quick`, `standard`, `detailed`).
- Analysis history per user.
- Bundled static frontend served at `/site`.
- Interactive API docs at `/docs`.

## Tech stack

- FastAPI + Uvicorn (ASGI server)
- SQLAlchemy + aiosqlite (async ORM over SQLite)
- Groq API (`llama-3.3-70b-versatile`) for LLM analysis
- python-jose + bcrypt for JWT auth and password hashing
- pypdf for PDF text extraction

## Project structure

```
backend-final/
├── app/
│   ├── main.py              # FastAPI app, CORS, router registration, static mount
│   ├── config.py            # Settings (API keys, JWT, storage, limits)
│   ├── database.py          # Async engine, session, init_db
│   ├── models.py            # User, Document, Analysis, AnalysisReport ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py          # /auth signup, login, me
│   │   ├── documents.py     # /documents upload, list, get, delete
│   │   └── analysis.py      # /analysis create, get, list
│   └── services/
│       ├── auth.py          # Password hashing, JWT, current-user dependency
│       ├── storage.py       # Local file storage
│       ├── pdf_extractor.py # PDF text extraction + word count
│       └── llm_service.py   # Groq API calls: analysis + similar-case retrieval
├── static/                  # Frontend (index.html) served at /site
├── uploads/                 # Uploaded files (local storage)
├── requirements.txt
├── SETUP.bat                # One-time environment setup (Windows)
└── START.bat                # Start the dev server (Windows)
```

## Getting started

### Prerequisites

- Python 3.10+
- A Groq API key (https://console.groq.com)

### Setup (Windows)

```bat
SETUP.bat
```

This creates a virtual environment and installs dependencies.

### Setup (manual / cross-platform)

```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### Run

```bat
START.bat
```

Or manually:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Then open:

- Website: http://localhost:8000/site
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Configuration

Settings live in `app/config.py`:

| Setting | Description | Default |
|---------|-------------|---------|
| `groq_api_key` | Groq API key for LLM calls | — |
| `groq_model` | Model name | `llama-3.3-70b-versatile` |
| `jwt_secret_key` | Secret for signing JWTs | — |
| `jwt_access_token_expire_minutes` | Token lifetime | `60` |
| `max_file_size_mb` | Upload size limit | `10` |
| `local_upload_dir` | Local storage path | `./uploads` |

> **Security note:** The current `config.py` hardcodes the Groq API key and JWT secret for local development. Before pushing to a public repo or deploying, move these to environment variables (e.g. via `pydantic-settings` / a `.env` file) and **rotate any key that has already been committed** — treat a committed key as compromised.

## API overview

Base path: `/api/v1`

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Log in, returns JWT access token |
| GET | `/auth/me` | Get current user profile |

### Documents

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/documents/upload` | Upload a PDF/TXT file (multipart) |
| GET | `/documents/` | List your documents (paginated) |
| GET | `/documents/{document_id}` | Get a document |
| DELETE | `/documents/{document_id}` | Soft-delete a document |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analysis/` | Analyze a `document_id` or raw `text` |
| GET | `/analysis/{analysis_id}` | Get an analysis result |
| GET | `/analysis/` | List your analyses |

All document and analysis endpoints require a `Authorization: Bearer <token>` header.

### Example flow

```bash
# 1. Sign up
curl -X POST http://localhost:8000/api/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123","full_name":"Test User"}'

# 2. Log in and grab the token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secret123"}'

# 3. Analyze raw text
curl -X POST http://localhost:8000/api/v1/analysis/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"text":"<at least 50 characters of case text>","language":"English","depth":"standard"}'
```

## Notes and limitations

- SQLite is used for simplicity; swap the database URL in `app/database.py` for Postgres in production.
- CORS is currently open to all origins (`*`) for local development — restrict this before deploying.
- LLM output depends on the Groq model and is truncated to the first ~6000 characters of the document for analysis.
- Verdict predictions are AI-generated and for informational purposes only — not legal advice.

## License

Add a license of your choice (e.g. MIT) before publishing.
