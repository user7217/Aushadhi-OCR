import axios from "axios";
import type { InferResp } from "../types/api";

export async function infer(
  file: File,
  params?: { top_k?: number; threshold?: number; ocr_backend?: "roboflow" | "easyocr"; enable_vision?: boolean }
) {
  const form = new FormData();
  form.append("file", file);
  if (params?.top_k !== undefined) form.append("top_k", String(params.top_k));
  if (params?.threshold !== undefined) form.append("threshold", String(params.threshold));
  form.append("ocr_backend", params?.ocr_backend ?? "roboflow");
  form.append("enable_vision", String(!!params?.enable_vision));

  const { data } = await axios.post<InferResp>("/api/infer", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return data;
}
