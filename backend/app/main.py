import os
import io
import asyncio
from typing import List

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from PIL import Image
import pandas as pd

from .config import settings
from .matching.fuzzy import normalize_text, fuzzy_topk, suspicious_tweaks, Match as FuzzyMatch
from .schemas.responses import Match as SchemaMatch, InferenceResponse
from .ocr.roboflow import detect_crops_then_ocr, ocr_direct
from .ocr.easyocr_backend import easyocr_run

app = FastAPI(title="Aushadhi-OCR")  # Response shaping respects response_model definitions in FastAPI. [web:229]

# CORS
if settings.ALLOW_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )  # FastAPI includes only fields defined by the response model at serialization. [web:229]

# Data loading
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")  # Ensure consistent relative path. [web:229]
MEDS_CSV = os.path.join(DATA_DIR, "meds.csv")  # CSV must contain product_name,strength,manufacturer,form,main_uses headers. [web:229]
if not os.path.exists(MEDS_CSV):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(MEDS_CSV, "w") as f:
        f.write("product_name,strength,manufacturer,form,main_uses\n")  # Seed with correct headers if missing. [web:229]
MEDS_DF = pd.read_csv(MEDS_CSV, dtype=str).fillna("")  # Read as strings and fill NaNs. [web:272]
MEDS_DF.columns = MEDS_DF.columns.str.strip()  # Strip any whitespace from headers to match dict-style access. [web:269]

@app.post("/api/infer", response_model=InferenceResponse)
async def infer(
    file: UploadFile = File(...),
    top_k: int = Form(5),
    threshold: float = Form(85.0),
    ocr_backend: str = Form("roboflow")
):
    # Read and prepare image
    raw = await file.read()  # UploadFile read for form/multipart is standard with FastAPI. [web:229]
    img = Image.open(io.BytesIO(raw)).convert("RGB")  # Convert to RGB for OCR backends. [web:229]

    # Run OCR
    if ocr_backend == "roboflow" and settings.ROBOFLOW_API_KEY:
        text = await detect_crops_then_ocr(img, settings)  # Use remote/backend OCR if configured. [web:229]
        if not text:
            text = await ocr_direct(img, settings)  # Fallback if detection yields no text. [web:229]
    else:
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, easyocr_run, img)  # Run local EasyOCR in a thread pool. [web:229]

    # Normalize OCR text for matching
    norm = normalize_text(text)  # Normalization aligns OCR text with dataset tokens. [web:229]
    if not norm:
        # Short-circuit when OCR found nothing
        return InferenceResponse(
            ocr_text=text,
            top_k=[],
            mismatch_flag=True,
            flags=["No text found by OCR"],
            main_uses=""
        )  # Response fields must exist in the Pydantic model to be serialized. [web:229]

    # Fuzzy match against both product_name and parsed strength aliases
    topk_fuzzy: List[FuzzyMatch] = fuzzy_topk(norm, MEDS_DF, k=top_k)  # fuzzy_topk aggregates best per row. [web:229]
    # Materialize SchemaMatch including form and main_uses for UI
    topk = [
        SchemaMatch(
            name=m.name,
            score=m.score,
            row_index=m.row_index,
            generic=MEDS_DF.iloc[m.row_index].get("strength", ""),
            manufacturer=MEDS_DF.iloc[m.row_index].get("manufacturer", ""),
            form=MEDS_DF.iloc[m.row_index].get("form", ""),
            alias_name="",
            main_uses=MEDS_DF.iloc[m.row_index].get("main_uses", ""),
        ) for m in topk_fuzzy
    ]  # Including these fields ensures they are present in the response JSON if defined in the model. [web:229]

    best = topk[0] if topk else None  # Select top match if any. [web:229]

    # Flags and mismatch heuristic
    flags: List[str] = []
    if best:
        flags += suspicious_tweaks(norm, normalize_text(best.name), best.score)  # Add heuristic flags. [web:229]
    mismatch = (not best) or (best.score < threshold) or bool(flags)  # Determine mismatch boolean. [web:229]

    # Shorten OCR text for display (trim noise)
    short_ocr_text = (text[:50] + '...') if len(text) > 50 else text  # Keep concise OCR text for UI. [web:229]

    # Return response; FastAPI filters to response_model fields only
    return InferenceResponse(
        ocr_text=short_ocr_text,
        top_k=topk,
        mismatch_flag=mismatch,
        flags=flags,
        main_uses=best.main_uses if best else ""
    )  # If fields are missing from the model, they won’t appear in the response. [web:229]

# Serve built SPA at root if present
FRONTEND_BUILD = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")  # Path to SPA build. [web:229]
if os.path.exists(os.path.join(FRONTEND_BUILD, "index.html")):
    app.mount("/", StaticFiles(directory=FRONTEND_BUILD, html=True), name="frontend")  # Starlette StaticFiles at root. [web:229]
