import os
import io
import asyncio
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
from PIL import Image
import pandas as pd

from .config import settings
from .matching.fuzzy import normalize_text, fuzzy_topk, suspicious_tweaks, Match as FuzzyMatch
from .schemas.responses import Match as SchemaMatch, InferenceResponse
from .ocr.roboflow import detect_crops_then_ocr, ocr_direct
from .ocr.easyocr_backend import easyocr_run

app = FastAPI(title="Aushadhi-OCR")

if settings.ALLOW_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
MEDS_CSV = os.path.join(DATA_DIR, "meds.csv")
if not os.path.exists(MEDS_CSV):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MEDS_CSV, "w") as f:
        f.write("product_name,strength,manufacturer,form,alias_name,main_uses\n")
MEDS_DF = pd.read_csv(MEDS_CSV, dtype=str).fillna("")

@app.post("/api/infer", response_model=InferenceResponse)
async def infer(
    file: UploadFile = File(...),
    top_k: int = Form(5),
    threshold: float = Form(85.0),
    ocr_backend: str = Form("roboflow")
):
    raw = await file.read()
    img = Image.open(io.BytesIO(raw)).convert("RGB")

    if ocr_backend == "roboflow" and settings.ROBOFLOW_API_KEY:
        text = await detect_crops_then_ocr(img, settings)
        if not text:
            text = await ocr_direct(img, settings)
    else:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, easyocr_run, img)

    norm = normalize_text(text)
    if not norm:
        return InferenceResponse(ocr_text=text, top_k=[], mismatch_flag=True, flags=["No text found by OCR"])

    topk_fuzzy: List[FuzzyMatch] = fuzzy_topk(norm, MEDS_DF, k=top_k)
    topk = [
        SchemaMatch(
            name=m.name,
            score=m.score,
            row_index=m.row_index,
            generic=MEDS_DF.iloc[m.row_index].get("strength", ""),
            manufacturer=MEDS_DF.iloc[m.row_index].get("manufacturer", ""),
            form=MEDS_DF.iloc[m.row_index].get("form", ""),
            alias_name="",  # aliases parsed internally in fuzzy_topk
            main_uses=MEDS_DF.iloc[m.row_index].get("main_uses", ""),
        ) for m in topk_fuzzy
    ]
    best = topk[0] if topk else None
    flags: List[str] = []
    if best:
        flags += suspicious_tweaks(norm, normalize_text(best.name), best.score)

    mismatch = (not best) or (best.score < threshold) or bool(flags)
    return InferenceResponse(ocr_text=text, top_k=topk, mismatch_flag=mismatch, flags=flags)

FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(os.path.join(FRONTEND_BUILD, "index.html")):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="frontend")
