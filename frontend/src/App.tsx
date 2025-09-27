import { useState, useCallback, useMemo } from "react";
import { Dropzone } from "./components/Dropzone";
import { infer } from "./lib/api";
import { downscale } from "./lib/image";
import type { InferResp } from "./types/api";

export default function App() {
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resp, setResp] = useState<InferResp | null>(null);
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback(async (files: File[]) => {
    setError(null);
    setResp(null);
    if (!files.length) return;
    const file = files[0];
    setLoading(true);
    try {
      const blob = await downscale(file, 1280);
      const previewUrl = URL.createObjectURL(blob);
      setPreview(previewUrl);
      const named = new File([blob], file.name.replace(/\.\w+$/, ".jpg"), { type: "image/jpeg" });
      const data = await infer(named, { top_k: 5, threshold: 85, ocr_backend: "roboflow" });
      setResp(data);
    } catch (e: any) {
      setError(e?.message || "Upload failed");
    } finally {
      setLoading(false);
    }
  }, []);

  const status = useMemo(() => {
    if (loading) return "Analyzing…";
    if (error) return `Error: ${error}`; // fixed: proper template literal
    if (!resp) return "Drop a medicine box photo";
    return resp.mismatch_flag ? "Potential mismatch" : "Likely valid";
  }, [loading, error, resp]);

  return (
    <div style={{ maxWidth: 920, margin: "0 auto", fontFamily: "Inter, system-ui" }}>
      <h2>Aushadhi‑OCR</h2>

      <Dropzone onDrop={onDrop} />

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
          {resp.flags.length > 0 && (
            <div style={{ color: "#b10" }}>
              Flags: {resp.flags.join(" • ")}
            </div>
          )}
          <h4>Top candidates</h4>
          <ul>
            {resp.top_k.map((m, i) => (
              <li key={i}>
                {m.name} — {m.score.toFixed(1)}% {m.generic ? `— ${m.generic}` : ""} {m.manufacturer ? `— ${m.manufacturer}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
