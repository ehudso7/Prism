"use client";

import { useState } from "react";
import { ingestText } from "../lib/api";

export default function Home() {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  async function go() {
    setLoading(true);
    try {
      const { media_id } = await ingestText(text);
      window.location.href = `/media/${media_id}`;
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={{ maxWidth: 900, margin: "40px auto", padding: 16 }}>
      <h1 style={{ fontSize: 34, marginBottom: 8 }}>PRISM</h1>
      <p style={{ marginBottom: 16 }}>
        Paste text now (Step 2 adds YouTube/articles/audio). Then switch lenses with receipts.
      </p>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={12}
        style={{ width: "100%", padding: 12, fontSize: 14 }}
        placeholder="Paste any text..."
      />

      <button
        onClick={go}
        disabled={loading || text.trim().length < 20}
        style={{ marginTop: 12, padding: "10px 14px", fontSize: 16 }}
      >
        {loading ? "Ingesting..." : "Create Media"}
      </button>
    </main>
  );
}
