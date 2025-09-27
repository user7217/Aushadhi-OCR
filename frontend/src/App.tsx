import { useState, useCallback, useMemo } from "react";
import { infer } from "./lib/api";
import type { InferResp, Match } from "./types/api";

const Pill = ({ text, tone = "#eef" }: { text: string; tone?: string }) => (
  <span style={{ background: tone, padding: "2px 8px", borderRadius: 999, fontSize: 12, marginRight: 8 }}>
    {text}
  </span>
);

export default function App() {
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState<InferResp | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enableVision, setEnableVision] = useState(false);

  const onFile = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null); setResp(null);
    const f = e.target.files?.[0]; if (!f) return;
    setLoading(true);
    try {
      setPreview(URL.createObjectURL(f));
      const data = await infer(f, { top_k: 5, threshold: 85, ocr_backend: "roboflow", enable_vision: enableVision });
      setResp(data);
    } catch (err: any) {
      setError(err?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }, [enableVision]);

  const status = useMemo(() => {
    if (loading) return "Analyzing…";
    if (error) return `Error: ${error}`;
    if (!resp) return "Upload a medicine image to begin";
    return resp.mismatch_flag ? "Potential mismatch" : "Likely valid";
  }, [loading, error, resp]);

  const top: Match | undefined = resp?.top_k?.[0];

  return (
    <div style={{ maxWidth: 980, margin: "0 auto", fontFamily: "Inter, system-ui", padding: 16 }}>
      <h2 style={{ marginBottom: 8 }}>Aushadhi‑OCR</h2>

      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <input type="file" accept="image/*" onChange={onFile} />
        <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 14 }}>
          <input type="checkbox" checked={enableVision} onChange={e => setEnableVision(e.target.checked)} />
          Run visual check
        </label>
      </div>

      {preview && (
        <div style={{ marginTop: 16, display: "grid", gridTemplateColumns: "320px 1fr", gap: 16 }}>
          <img src={preview} alt="preview" style={{ width: 320, borderRadius: 8, border: "1px solid #ddd" }} />
          <div>
            <div style={{ marginBottom: 8 }}><strong>Status:</strong> {status}</div>
            {resp && (
              <>
                <div style={{ color: "#666", fontSize: 14, marginBottom: 12 }}>
                  <strong>OCR:</strong> {resp.ocr_text || "(none)"}
                </div>

                {top && (
                  <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 14, boxShadow: "0 1px 2px rgba(0,0,0,0.04)" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
                      <div style={{ fontSize: 20, fontWeight: 700 }}>{top.name}</div>
                      <div style={{ color: "#777", fontSize: 12 }}>Score {top.score.toFixed(1)}%</div>
                    </div>

                    <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 8 }}>
                      {top.form && <Pill text={`Form: ${top.form}`} />}
                      {top.generic && <Pill text={`Strength: ${top.generic}`} />}
                      {top.manufacturer && <Pill text={`Mfr: ${top.manufacturer}`} tone="#efe" />}
                    </div>

                    <div style={{ marginTop: 10 }}>
                      <div style={{ fontSize: 13, color: "#444" }}><strong>Uses:</strong> {resp.main_uses || top.main_uses || "(Not available)"}</div>
                    </div>

                    {(resp.edit_distance !== undefined || resp.vision_score !== undefined) && (
                      <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
                        {typeof resp.edit_distance === "number" && <Pill tone="#fee" text={`Edit distance: ${resp.edit_distance}`} />}
                        {typeof resp.vision_score === "number" && <Pill tone="#eef" text={`Visual similarity: ${resp.vision_score.toFixed(1)}%`} />}
                      </div>
                    )}

                    {resp.flags.length > 0 && (
                      <div style={{ marginTop: 10, fontSize: 13, color: "#b10" }}>
                        {resp.flags.map((f, i) => <div key={i}>• {f}</div>)}
                      </div>
                    )}
                  </div>
                )}

                {resp?.top_k && resp.top_k.length > 1 && (
                  <div style={{ marginTop: 16 }}>
                    <div style={{ fontWeight: 600, marginBottom: 6 }}>Other candidates</div>
                    <div style={{ display: "grid", gap: 8 }}>
                      {resp.top_k.slice(1).map((m, i) => (
                        <div key={i} style={{ border: "1px dashed #e5e7eb", borderRadius: 8, padding: 10 }}>
                          <div style={{ display: "flex", justifyContent: "space-between" }}>
                            <div style={{ fontWeight: 600 }}>{m.name}</div>
                            <div style={{ color: "#777", fontSize: 12 }}>{m.score.toFixed(1)}%</div>
                          </div>
                          <div style={{ marginTop: 4, fontSize: 13, color: "#555" }}>
                            {[m.form, m.generic, m.manufacturer, m.main_uses].filter(Boolean).join(" • ")}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
