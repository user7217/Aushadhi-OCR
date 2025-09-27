import { useDropzone } from "react-dropzone";
import { useCallback } from "react";

export function Dropzone({ onDrop }: { onDrop: (files: File[]) => void }) {
  const cb = useCallback((files: File[]) => onDrop(files), [onDrop]);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: cb, multiple: false, accept: { "image/*": [] }
  });

  return (
    <div {...getRootProps()} style={{
      padding: 24, border: "2px dashed #888", borderRadius: 12, textAlign: "center",
      background: isDragActive ? "#f0f8ff" : "#fafafa", cursor: "pointer"
    }}>
      <input {...getInputProps()} />
      <p>{isDragActive ? "Drop the image…" : "Drag & drop, or click to select a photo"}</p>
    </div>
  );
}
