"use client";

import { useEffect, useMemo, useState } from "react";
import { listLenses, runLens, getRun } from "../../../lib/api";

export default function MediaPage({ params }: { params: { id: string } }) {
  const mediaId = params.id;
  const [lenses, setLenses] = useState<Array<any>>([]);
  const [selected, setSelected] = useState<string>("");
  const [runId, setRunId] = useState<string>("");
  const [run, setRun] = useState<any>(null);
  const [err, setErr] = useState<string>("");

  useEffect(() => {
    listLenses().then((ls) => {
      setLenses(ls);
      if (ls[0]) setSelected(ls[0].id);
    }).catch(e => setErr(String(e)));
  }, []);

  async function startRun() {
    setErr("");
    setRun(null);
    const { run_id } = await runLens(mediaId, selected);
    setRunId(run_id);
  }

  useEffect(() => {
    if (!runId) return;
    let alive = true;
    const t = setInterval(async () => {
      const r = await getRun(runId);
      if (!alive) return;
      setRun(r);
      if (r.status === "done" || r.status === "error") clearInterval(t);
    }, 1500);
    return () => { alive = false; clearInterval(t); };
  }, [runId]);

  const selectedLens = useMemo(() => lenses.find(l => l.id === selected), [lenses, selected]);

  return (
    <main style={{ maxWidth: 1100, margin: "30px auto", padding: 16 }}>
      <h1 style={{ fontSize: 28, marginBottom: 6 }}>Media: {mediaId}</h1>
      <p style={{ marginBottom: 16 }}>Choose a lens. Run it. View results + receipts.</p>

      {err && <div style={{ padding: 12, background: "#fee", marginBottom: 12 }}>{err}</div>}

      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
        <select value={selected} onChange={(e) => setSelected(e.target.value)} style={{ padding: 10 }}>
          {lenses.map(l => <option key={l.id} value={l.id}>{l.name}</option>)}
        </select>
        <button onClick={startRun} style={{ padding: "10px 14px" }}>
          Run Lens
        </button>
        {selectedLens?.description && <span style={{ opacity: 0.8 }}>{selectedLens.description}</span>}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
          <h2 style={{ marginTop: 0 }}>Result</h2>
          {!run && <p>Run a lens to see output.</p>}
          {run?.status === "queued" || run?.status === "running" ? <p>Status: {run.status}…</p> : null}
          {run?.status === "error" ? <pre>{run.error}</pre> : null}
          {run?.status === "done" ? (
            <pre style={{ whiteSpace: "pre-wrap" }}>{String(run.result)}</pre>
          ) : null}
        </section>

        <section style={{ border: "1px solid #ddd", borderRadius: 8, padding: 12 }}>
          <h2 style={{ marginTop: 0 }}>Receipts</h2>
          <p style={{ opacity: 0.75 }}>
            Step 2 will parse JSON and render clickable timestamp receipts.
            For now, you'll see raw output (still useful to validate end-to-end).
          </p>
        </section>
      </div>
    </main>
  );
}
