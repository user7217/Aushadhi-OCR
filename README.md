# Aushadhi‑OCR

Backend: FastAPI + Roboflow OCR + EasyOCR fallback. Frontend: Vite React TS.

Dev quickstart:
- cd backend && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
- uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
- In another terminal: cd frontend && npm i && npm run dev

Prod-like:
- cd frontend && npm run build
- Restart backend; FastAPI serves frontend/dist at "/".
