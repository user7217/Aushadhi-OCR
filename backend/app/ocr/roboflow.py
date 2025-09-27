from typing import List, Tuple, Optional
import numpy as np
from PIL import Image

# Reuse your existing client init
# from inference_sdk import InferenceHTTPClient
# def get_client(api_key: str):
#     return InferenceHTTPClient(api_url="https://detect.roboflow.com", api_key=api_key)

def _pil_to_np(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("RGB"))

def _iou_xywh(box_a, box_b):
    # boxes in (cx, cy, w, h)
    ax1 = box_a[0] - box_a[2] / 2.0
    ay1 = box_a[1] - box_a[3] / 2.0
    ax2 = box_a[0] + box_a[2] / 2.0
    ay2 = box_a[1] + box_a[3] / 2.0
    bx1 = box_b[0] - box_b[2] / 2.0
    by1 = box_b[1] - box_b[3] / 2.0
    bx2 = box_b[0] + box_b[2] / 2.0
    by2 = box_b[1] + box_b[3] / 2.0

    inter_w = max(0.0, min(ax2, bx2) - max(ax1, bx1))
    inter_h = max(0.0, min(ay2, by2) - max(ay1, by1))
    inter = inter_w * inter_h
    area_a = (ax2 - ax1) * (ay2 - ay1)
    area_b = (bx2 - bx1) * (by2 - by1)
    union = max(1e-6, area_a + area_b - inter)
    return inter / union

def _nms_xywh(
    dets: List[Tuple[float, Tuple[int,int,int,int]]],
    iou_thr: float = 0.5
) -> List[Tuple[float, Tuple[int,int,int,int]]]:
    # dets: list of (score, (cx,cy,w,h))
    dets_sorted = sorted(dets, key=lambda x: x[0], reverse=True)
    keep: List[Tuple[float, Tuple[int,int,int,int]]]= []
    for s, b in dets_sorted:
        drop = False
        for s2, b2 in keep:
            if _iou_xywh(b, b2) > iou_thr:
                drop = True
                break
        if not drop:
            keep.append((s, b))
    return keep

def detect_medicine_boxes(
    img: Image.Image,
    settings,
    conf: float = 0.65,
    class_filter: Optional[List[str]] = None,
    min_area_ratio: float = 0.02,
    iou_thr: float = 0.5
) -> List[Tuple[float, Tuple[int, int, int, int]]]:
    """
    Run Roboflow detection and return filtered boxes:
    - class allowlist
    - confidence >= conf (default 0.65)
    - area >= min_area_ratio * image_area (default 2%)
    - NMS with IoU threshold (default 0.5)
    Returns: list of (score, (cx, cy, w, h))
    """
    if not getattr(settings, "ROBOFLOW_API_KEY", None) or not getattr(settings, "ROBOFLOW_MODEL_ID", None):
        return []

    try:
        client = get_client(settings.ROBOFLOW_API_KEY)
        result = client.infer(_pil_to_np(img), model_id=settings.ROBOFLOW_MODEL_ID)
    except Exception:
        return []

    preds = result.get("predictions", []) or result.get("preds", [])
    if not preds:
        return []

    W, H = img.size
    img_area = float(W * H)
    allowed = set(class_filter or getattr(settings, "ROBOFLOW_CLASSES", ["medicine","box","strip","blister","bottle"]))
    rough: List[Tuple[float, Tuple[int,int,int,int]]] = []

    for p in preds:
        cls = p.get("class") or p.get("label") or ""
        score = p.get("confidence") or p.get("score") or 0
        if score is None:
            continue
        try:
            score = float(score)
        except Exception:
            continue
        if score < conf:
            continue
        if allowed and cls not in allowed:
            continue

        if not all(k in p for k in ("x","y","width","height")):
            continue
        cx, cy, w, h = float(p["x"]), float(p["y"]), float(p["width"]), float(p["height"])
        area_ratio = (w * h) / img_area
        if area_ratio < min_area_ratio:
            continue
        rough.append((score, (int(cx), int(cy), int(w), int(h))))

    if not rough:
        return []

    # NMS
    kept = _nms_xywh(rough, iou_thr=iou_thr)
    return kept

# Existing EasyOCR import used by crops OCR
# Do local import in function to avoid circulars
async def detect_crops_then_ocr(
    img: Image.Image,
    settings,
    use_preprocess: bool = False,
    use_adaptive_threshold: bool = False,
    crop_ocr_backend: str = "easyocr"
) -> str:
    """
    Detection-gated OCR:
    - Run Roboflow detection with strict filters
    - If no valid boxes, return ""
    - Else OCR the detected crops only and join text
    """
    from .preprocess import preprocess_for_ocr
    from ..ocr.easyocr_backend import easyocr_run
    import asyncio

    boxes = detect_medicine_boxes(
        img,
        settings,
        conf=0.65,
        class_filter=getattr(settings, "ROBOFLOW_CLASSES", None),
        min_area_ratio=0.02,
        iou_thr=0.5
    )
    if not boxes:
        return ""

    W, H = img.size
    # Sort by x center for consistent read order
    boxes = sorted(boxes, key=lambda x: x[1][0])

    texts: List[str] = []
    for score, (cx, cy, bw, bh) in boxes:
        x1 = max(0, int(cx - bw / 2)); y1 = max(0, int(cy - bh / 2))
        x2 = min(W, int(cx + bw / 2)); y2 = min(H, int(cy + bh / 2))
        crop = img.crop((x1, y1, x2, y2))
        if use_preprocess:
            crop = preprocess_for_ocr(crop, enable_threshold=use_adaptive_threshold)

        if crop_ocr_backend == "easyocr":
            loop = asyncio.get_event_loop()
            t = await loop.run_in_executor(None, easyocr_run, crop)
        else:
            # If you have another OCR backend, plug here; default to EasyOCR
            loop = asyncio.get_event_loop()
            t = await loop.run_in_executor(None, easyocr_run, crop)

        if t and t.strip():
            texts.append(t.strip())

    joined = " ".join(texts)
    # Minimal signal guard: if too short, treat as no OCR
    if len(joined.strip()) < 12:
        return ""
    return joined
