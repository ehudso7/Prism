# PRISM

**Perspective Layers + Receipts** - A web app that lets you switch between different viewpoints on any content, with every claim backed by exact timestamps, quotes, or text spans.

## What it does

Paste text (or later, YouTube URLs/articles/audio), and instantly switch between viewpoints like:
- **Beginner** - Explain simply, define terms, reduce jargon
- **Skeptic** - Challenge assumptions, identify missing info and weak logic
- **Coach** - Turn content into practical tactics and training cues

Every claim is backed by **receipts**: exact timestamps, quotes, or text spans.

## Quick Start

### Prerequisites
- Docker & Docker Compose (or local Postgres + Redis)
- Python 3.11+
- Node.js 18+
- OpenAI API key (or compatible LLM API)

### Using Docker Compose

```bash
# Start Postgres and Redis
docker compose up -d

# Start API (Terminal 1)
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="postgresql://prism:prism@localhost:5432/prism"
export REDIS_URL="redis://localhost:6379/0"
export LLM_API_KEY="your-openai-api-key"
uvicorn main:app --reload --port 8000

# Start Worker (Terminal 2)
cd apps/api
source .venv/bin/activate
export DATABASE_URL="postgresql://prism:prism@localhost:5432/prism"
export REDIS_URL="redis://localhost:6379/0"
export LLM_API_KEY="your-openai-api-key"
rq worker prism

# Start Frontend (Terminal 3)
cd apps/web
npm install
export NEXT_PUBLIC_API_BASE="http://localhost:8000"
npm run dev
```

### Access
- Web UI: http://localhost:3000
- API Docs: http://localhost:8000/docs

## Architecture

- **Frontend**: Next.js (TypeScript)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Queue**: Redis + RQ worker
- **LLM**: OpenAI-compatible API

## API Endpoints

- `POST /api/media/ingest` - Ingest text/URL/audio
- `GET /api/media/{media_id}` - Get media details
- `GET /api/lenses` - List available lenses
- `POST /api/media/{media_id}/run/{lens_id}` - Run a lens on media
- `GET /api/runs/{run_id}` - Get lens run status/results

## MVP Scope (v0.1)

### Supported Media
- Text (paste directly)
- YouTube URL (Step 2)
- Web article URL (Step 2)
- Audio upload (Step 2)

### Output per lens
- Headline
- 6-10 bullet takeaways
- 3-8 receipts (timestamped quotes/spans)
- "What's missing / counterpoints"
- Action items (optional)
