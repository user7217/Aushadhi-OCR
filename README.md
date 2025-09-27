# Aushadhi‑OCR

Identify medicines from packaging photos and return the most useful facts fast: Form (e.g., Tablet, Cream) and Main Uses, with a strict detection gate that prevents false matches on non‑medicine images.

## Key features

- Detection‑gated OCR: runs object detection first; OCR happens only on detected medicine crops to avoid “guessing” on irrelevant images.  
- Robust matching: blends token‑set and partial fuzzy ratios over product names and strength aliases to handle noisy OCR text.  
- Actionable output: returns Form and Main Uses from a curated CSV; also surfaces flags for borderline cases.  

## Architecture

- Backend: FastAPI service that handles upload, runs detection‑gated OCR, normalizes text, and fuzzy‑matches against a medicines CSV.  
- OCR: Detect first; if boxes exist, OCR cropped regions; for local mode, EasyOCR with optional conservative preprocessing.  
- Matching: product_name plus strength split into aliases (e.g., “+”, “;”); blends token_set_ratio and partial_ratio; returns top‑K ranked matches.  
- Frontend: React + TypeScript SPA; shows preview, status, a polished top‑match card (Form, Strength, Manufacturer, Uses), and alternates.

## Data model

- CSV columns:  
  - product_name  
  - strength (can include multiple aliases separated by “;”, “+”, or “,”)  
  - manufacturer  
  - form  
  - main_uses  
- API response (core fields):  
  - ocr_text: short snippet for context  
  - top_k: array of candidates with name, score, generic (strength), manufacturer, form, main_uses  
  - mismatch_flag and flags: for threshold bands and fraud/tamper heuristics  
  - main_uses: convenience copy of the top match’s uses  

## Setup

1) Clone and install
- Create a Python virtual environment.  
- Install backend dependencies (FastAPI, Uvicorn, pandas, Pillow, RapidFuzz, EasyOCR, and OpenCV headless).  
- Install frontend dependencies (React, TypeScript, build tool).

2) Environment
- Add a config for:  
  - ROBOFLOW_API_KEY (if using detection gate)  
  - ROBOFLOW_MODEL_ID (the detection model)  
  - ROBOFLOW_CLASSES (optional; default allowlist includes “medicine”, “box”, “strip”, “blister”, “bottle”)  
  - CORS settings as needed

3) Dataset
- Place meds.csv at backend/app/data/meds.csv.  
- Ensure headers exactly: product_name,strength,manufacturer,form,main_uses.

## Run

Backend
- Start the API server (development):  
  - uvicorn backend.app.main:app --reload  
- The API will also serve the frontend if the production build is present under frontend/dist.

Frontend
- Build the SPA:  
  - cd frontend && npm run build  
- Open the served root path to access the UI.

## Usage

- Upload a photo of a medicine package.  
- The detector gates the request:  
  - If no medicine‑like detection passes class, confidence, area, and NMS filters, the API returns “No medicine detected by gate.”  
  - If detections exist, OCR runs on those crops and merges text.  
- The app shows:  
  - Status (Likely valid vs Potential mismatch)  
  - OCR snippet  
  - Top match card with Form, Strength, Manufacturer, and Uses  
  - Other candidates with scores for verification

## How it works

- Detection gate: medicine‑like objects must be detected with sufficient confidence and reasonable size; overlapping boxes are suppressed.  
- OCR on crops: running OCR only on detected boxes improves signal and avoids reading random background text.  
- Normalization: lowercasing, diacritic stripping, unit standardization (e.g., mg/mcg/%), and safe punctuation retention to handle multi‑ingredient strings.  
- Matching: strengths are split into aliases; fuzzy scoring blends token‑set and partial ratios to rank candidates robustly; threshold bands control acceptance vs review.  

## Configuration tips

- Tighten or relax detection by adjusting:  
  - Confidence (start ~0.65)  
  - Minimum area ratio (start ~0.02)  
  - NMS IoU threshold (~0.5)  
- If the detector is missing true positives, consider lowering confidence or area threshold slightly; if it’s too permissive, raise them.  
- For local OCR, enable conservative preprocessing only for tough lighting; avoid aggressive binarization by default to protect fine print.

## Extensibility

- Visual similarity: add image embeddings (e.g., CLIP) to compute packaging similarity and flag low scores for tamper/spoof detection.  
- Lexicon correction: build brand/active ingredient lexicons from the CSV to auto‑correct OCR tokens by small edit distance before matching.  
- Field‑aware boosts: reward dosage and form overlaps only when reliably present in OCR to break ties among close candidates.  
- Admin loop: capture borderline cases (mid‑band scores) and enrich aliases or adjust thresholds regularly.

## API summary

Endpoint
- POST /api/infer  
  - multipart/form-data with file, optional params:
    - top_k (default 5)  
    - threshold (default 80)  
    - ocr_backend (“roboflow” or local mode)  
    - use_preprocess (bool)  
    - use_adaptive_threshold (bool)  

Response
- JSON with ocr_text, top_k, mismatch_flag, flags, main_uses.

## Troubleshooting

- “No medicine detected by gate”:  
  - Ensure ROBOFLOW_API_KEY and model ID are set; verify class names; tune confidence/area/NMS.  
- Form/Uses not visible:  
  - Confirm CSV headers match exactly; ensure backend response models include form and main_uses; check Network tab for the fields.  
- Recognition regressed:  
  - Disable preprocessing; try alternate OCR backend; verify detector thresholds; compare raw OCR text length.  

## License

- Specify your preferred license here.

## Acknowledgments

- Thanks to the open‑source OCR, matching, and web frameworks that make this possible.

[1](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-and-highlighting-code-blocks)
[2](https://www.markdownguide.org/extended-syntax/)
[3](https://www.codecademy.com/resources/docs/markdown/code-blocks)
[4](https://www.markdownguide.org/basic-syntax/)
[5](https://www.glukhov.org/post/2025/07/markdown-codeblocks/)
[6](https://www.freecodecamp.org/news/how-to-format-code-in-markdown/)
[7](https://learn.microsoft.com/en-us/azure/devops/project/wiki/markdown-guidance?view=azure-devops)
[8](https://www.jetbrains.com/help/hub/markdown-syntax.html)
[9](https://docs.github.com/github/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax)
[10](https://commonmark.org/help/tutorial/09-code.html)