const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export async function ingestText(text: string) {
  const r = await fetch(`${API_BASE}/api/media/ingest`, {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ type: "text", text })
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ media_id: string }>;
}

export async function listLenses() {
  const r = await fetch(`${API_BASE}/api/lenses`, { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<Array<{id:string; name:string; description?:string}>>;
}

export async function runLens(mediaId: string, lensId: string) {
  const r = await fetch(`${API_BASE}/api/media/${mediaId}/run/${lensId}`, { method: "POST" });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ run_id: string }>;
}

export async function getRun(runId: string) {
  const r = await fetch(`${API_BASE}/api/runs/${runId}`, { cache: "no-store" });
  if (!r.ok) throw new Error(await r.text());
  return r.json() as Promise<{ id:string; status:string; result?: any; error?: string }>;
}
