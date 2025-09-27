import io
from typing import List
from PIL import Image
from ..deps import get_inference_client
from ..config import settings

def pil_to_bytes(img: Image.Image, fmt="JPEG") -> bytes:
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()

async def detect_crops_then_ocr(img: Image.Image, cfg) -> str:
    if not cfg.DETECT_MODEL_ID or not settings.ROBOFLOW_API_KEY:
        return ""
    client = get_inference_client()
    if client is None:
        return ""
    det = await client.infer_from_api_v0_async(pil_to_bytes(img), model_id=cfg.DETECT_MODEL_ID)
    preds = det.get("predictions", []) if isinstance(det, dict) else []
    texts: List[str] = []
    w, h = img.size
    for p in preds[:6]:
        x0 = max(0, int(p["x"] - p["width"]/2))
        y0 = max(0, int(p["y"] - p["height"]/2))
        x1 = min(w, int(p["x"] + p["width"]/2))
        y1 = min(h, int(p["y"] + p["height"]/2))
        crop = img.crop((x0, y0, x1, y1))
        ocr = await client.ocr_image_async(pil_to_bytes(crop))
        txt = ocr.get("result", "") if isinstance(ocr, dict) else ""
        if txt:
            texts.append(txt)
    return " ".join(texts)

async def ocr_direct(img: Image.Image, cfg) -> str:
    client = get_inference_client()
    if client is None:
        return ""
    ocr = await client.ocr_image_async(pil_to_bytes(img))
    return ocr.get("result", "") if isinstance(ocr, dict) else ""
