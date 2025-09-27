import { useState, useCallback, useMemo } from "react";
import { infer } from "./lib/api";
import type { InferResp, Match } from "./types/api";

export default function App() {
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState<InferResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onFileChange = useCallback(async (ev: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setResp(null);
    const file = ev.target.files?.[0];
    if (!file) return;
    setLoading(true);
    try {
      const data = await infer(file, { top_k: 5, threshold: 85, ocr_backend: "roboflow" });
      setResp(data);
      const url = URL.createObjectURL(file);
      setPreview(url);
    } catch (e: any) {
      setError(e?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const status = useMemo(() => {
    if (loading) return "Analyzing…";
    if (error) return `Error: ${error}`;
    if (!resp) return "Upload a medicine image to begin";
    return resp.mismatch_flag ? "Potential mismatch" : "Likely valid";
  }, [loading, error, resp]);

  const top: Match | undefined = resp?.top_k?.[0];

  return (
    <div style={{ maxWidth: 920, margin: "0 auto", fontFamily: "Inter, system-ui" }}>
      <h2>Aushadhi‑OCR</h2>

      <input type="file" accept="image/*" onChange={onFileChange} />

      {preview && (
        <div style={{ marginTop: 16 }}>
          <img src={preview} alt="preview" style={{ maxWidth: "100%", borderRadius: 8 }} />
        </div>
      )}

      <div style={{ marginTop: 16 }}>
        <strong>Status:</strong> {status}
      </div>

      {resp && (
        <div style={{ marginTop: 16 }}>
          <div><strong>OCR:</strong> {resp.ocr_text || "(none)"} </div>

          {top && (
            <div style={{ marginTop: 12, padding: 12, border: "1px solid #ddd", borderRadius: 8 }}>
              <div style={{ fontSize: 18, fontWeight: 600 }}>{top.name}</div>
              {top.generic && <div style={{ color: "#555", marginTop: 4 }}>Strength: {top.generic}</div>}
              {top.form && <div style={{ color: "#555", marginTop: 4 }}>Form: {top.form}</div>}
              {top.manufacturer && <div style={{ color: "#555", marginTop: 4 }}>Manufacturer: {top.manufacturer}</div>}
              <div style={{ marginTop: 8 }}>
                <strong>Uses:</strong> {resp.main_uses || top.main_uses || "(Not available)"}
              </div>
              <div style={{ marginTop: 8, color: "#777" }}>
                Match score: {top.score.toFixed(1)}%
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
