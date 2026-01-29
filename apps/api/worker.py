import os
import uuid
from rq import Queue
from redis import Redis
from dotenv import load_dotenv
from db import get_conn
from llm import chat_completion

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

def redis_conn():
    return Redis.from_url(REDIS_URL)

q = Queue("prism", connection=redis_conn())

DEFAULT_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "takeaways": {"type": "array", "items": {"type": "string"}},
        "receipts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "segment_id": {"type": "string"},
                    "start_sec": {"type": ["integer", "null"]},
                    "end_sec": {"type": ["integer", "null"]},
                    "quote": {"type": "string"}
                },
                "required": ["segment_id", "quote"]
            }
        },
        "missing_or_counterpoints": {"type": "array", "items": {"type": "string"}},
        "action_items": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["headline", "takeaways", "receipts"]
}

def run_lens_job(run_id: str):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("update lens_runs set status='running' where id=%s", (run_id,))
        conn.commit()

        cur.execute("""
          select lr.id, lr.media_id, lr.lens_id, l.system_prompt
          from lens_runs lr join lenses l on l.id = lr.lens_id
          where lr.id=%s
        """, (run_id,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("run not found")

        media_id = row["media_id"]
        system_prompt = row["system_prompt"]

        cur.execute("select id, start_sec, end_sec, text from segments where media_id=%s order by idx asc limit 60", (media_id,))
        segs = cur.fetchall()

        # Build "evidence pack"
        evidence_lines = []
        for s in segs:
            evidence_lines.append(f"- SEGMENT {s['id']} [{s['start_sec']}..{s['end_sec']}]: {s['text'][:600]}")

        user_prompt = f"""
You must produce a viewpoint analysis using ONLY the evidence below.
Every key claim must be backed by RECEIPTS that reference segment_id.
Return JSON with keys: headline, takeaways, receipts, missing_or_counterpoints, action_items.
Evidence:
{chr(10).join(evidence_lines)}
"""

        try:
            raw = chat_completion(system=system_prompt, user=user_prompt)
            # Store raw as string if it isn't valid JSON; UI can still show it.
            # (You can tighten this later with JSON mode / schema validation.)
            cur.execute("update lens_runs set status='done', result=%s where id=%s", (raw, run_id))
            conn.commit()
        except Exception as e:
            cur.execute("update lens_runs set status='error', error=%s where id=%s", (str(e), run_id))
            conn.commit()
            raise
