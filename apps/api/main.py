import os, uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from db import get_conn
from models import IngestRequest, IngestResponse, Lens, RunResponse, RunStatus, Media
from worker import q, run_lens_job

load_dotenv()
app = FastAPI(title="PRISM API")

def stringify_uuids(row: dict) -> dict:
    """Convert UUID fields to strings for Pydantic compatibility."""
    return {k: str(v) if hasattr(v, 'hex') else v for k, v in row.items()}

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def seed_default_lenses():
    default_lenses = [
        {
            "name": "Beginner",
            "description": "Explain simply, define terms, reduce jargon.",
            "system_prompt": "You are an expert teacher. Explain clearly and simply. No fluff. Use receipts."
        },
        {
            "name": "Skeptic",
            "description": "Challenge assumptions; identify missing info and weak logic.",
            "system_prompt": "You are a rigorous skeptic. Identify weak claims and missing evidence. Use receipts."
        },
        {
            "name": "Coach",
            "description": "Turn content into practical tactics and training cues.",
            "system_prompt": "You are an elite coach. Extract actionable cues and drills. Use receipts."
        },
    ]
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("select count(*) as c from lenses")
        c = cur.fetchone()["c"]
        if c == 0:
            for d in default_lenses:
                lid = str(uuid.uuid4())
                cur.execute(
                    "insert into lenses (id, name, description, system_prompt, output_schema) values (%s,%s,%s,%s,%s)",
                    (lid, d["name"], d["description"], d["system_prompt"], '{"type":"object"}')
                )
            conn.commit()

@app.on_event("startup")
def startup():
    seed_default_lenses()

@app.post("/api/media/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest):
    media_id = str(uuid.uuid4())

    if req.type not in ["youtube", "article", "audio", "text"]:
        raise HTTPException(400, "invalid type")

    if req.type in ["youtube", "article"] and not req.source_url:
        raise HTTPException(400, "source_url required")

    if req.type == "text" and not req.text:
        raise HTTPException(400, "text required")

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            "insert into media (id, type, source_url, title, status) values (%s,%s,%s,%s,%s)",
            (media_id, req.type, req.source_url, None, "ready" if req.type=="text" else "ingested")
        )

        # MVP: if text, create segments immediately. For youtube/article/audio we'll add processors in Step 2.
        if req.type == "text":
            text = req.text.strip()
            chunks = [text[i:i+800] for i in range(0, len(text), 800)]
            for idx, ch in enumerate(chunks):
                sid = str(uuid.uuid4())
                cur.execute(
                    "insert into segments (id, media_id, idx, start_sec, end_sec, text) values (%s,%s,%s,%s,%s,%s)",
                    (sid, media_id, idx, None, None, ch)
                )
            cur.execute("update media set status='ready' where id=%s", (media_id,))
        conn.commit()

    return IngestResponse(media_id=media_id)

@app.get("/api/media/{media_id}", response_model=Media)
def get_media(media_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("select id, type, source_url, title, duration_sec, status from media where id=%s", (media_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "not found")
        return Media(**stringify_uuids(row))

@app.get("/api/lenses", response_model=list[Lens])
def list_lenses():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("select id, name, description from lenses order by created_at asc")
        rows = cur.fetchall()
        return [Lens(**stringify_uuids(r)) for r in rows]

@app.post("/api/media/{media_id}/run/{lens_id}", response_model=RunResponse)
def run_lens(media_id: str, lens_id: str):
    run_id = str(uuid.uuid4())
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("select id from media where id=%s", (media_id,))
        if not cur.fetchone():
            raise HTTPException(404, "media not found")
        cur.execute("select id from lenses where id=%s", (lens_id,))
        if not cur.fetchone():
            raise HTTPException(404, "lens not found")

        cur.execute(
            "insert into lens_runs (id, media_id, lens_id, status) values (%s,%s,%s,%s)",
            (run_id, media_id, lens_id, "queued")
        )
        conn.commit()

    q.enqueue(run_lens_job, run_id)
    return RunResponse(run_id=run_id)

@app.get("/api/runs/{run_id}", response_model=RunStatus)
def get_run(run_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("select id, status, result, error from lens_runs where id=%s", (run_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, "not found")
        return RunStatus(**stringify_uuids(row))
