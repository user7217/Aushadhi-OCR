import re
import unicodedata
from typing import List
import pandas as pd
from rapidfuzz import fuzz, process
from pydantic import BaseModel
from rapidfuzz.distance import Levenshtein

class Match(BaseModel):
    name: str
    score: float
    row_index: int
    generic: str | None = None
    manufacturer: str | None = None

UNIT_MAP = {
    "microgram": "mcg",
    "µg": "mcg",
    "μg": "mcg",
    "milligram": "mg",
    "grams": "g",
    "milliliter": "ml",
    "mls": "ml",
    "iu": "iu",
    "%": "%",
}

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def standardize_units(s: str) -> str:
    t = s
    for k, v in UNIT_MAP.items():
        t = t.replace(k, v)
    return t

def normalize_text(s: str) -> str:
    s = (s or "").lower()
    s = strip_accents(s)
    s = s.replace("-", " ")
    s = standardize_units(s)
    # keep + / ; , % for splitting and dosage parsing
    s = re.sub(r"[^a-z0-9\s+/;,+%]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _scorer(a: str, b: str, **kwargs) -> float:
    # Stable blend proven effective on mixed OCR
    ts = fuzz.token_set_ratio(a, b)
    pr = fuzz.partial_ratio(a, b)
    return 0.6 * ts + 0.4 * pr

def _row_candidates(row) -> list[str]:
    product_name = normalize_text(getattr(row, "product_name", "") or "")
    strength_raw = getattr(row, "strength", "") or ""
    aliases = [normalize_text(p) for p in re.split(r"[;,+]", strength_raw) if p and p.strip()]
    seen = set()
    out = []
    for t in aliases + [product_name]:
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return out if out else [product_name]

def fuzzy_topk(query: str, df: pd.DataFrame, k: int = 5) -> List[Match]:
    q = normalize_text(query)
    candidates: list[tuple[str, int, str]] = []
    for idx, row in enumerate(df.itertuples()):
        cands = _row_candidates(row)
        pname = getattr(row, "product_name", "") or ""
        for c in cands:
            candidates.append((c, idx, pname))
    if not candidates:
        return []
    names = [c[0] for c in candidates]
    matches = process.extract(q, names, scorer=_scorer, limit=max(k * 3, 15))

    best_per_row: dict[int, dict] = {}
    for _, score, pos in matches:
        row_idx = candidates[pos][1]
        pname = candidates[pos][2]
        sc = float(score)
        if row_idx not in best_per_row or sc > best_per_row[row_idx]["score"]:
            best_per_row[row_idx] = {"score": sc, "name": pname, "row_index": row_idx}

    ranked = sorted(best_per_row.values(), key=lambda x: x["score"], reverse=True)[:k]

    out: List[Match] = []
    for item in ranked:
        i = item["row_index"]
        row = df.iloc[i]
        out.append(Match(
            name=item["name"],
            score=item["score"],
            row_index=int(i),
            generic=str(row.get("strength", "")),
            manufacturer=str(row.get("manufacturer", "")) if "manufacturer" in row else None
        ))
    return out

def suspicious_tweaks(query: str, best_name: str, best_score: float) -> list[str]:
    flags: list[str] = []
    if best_score < 75:
        flags.append(f"Low similarity score {best_score:.1f}")
    q = (query or "").replace(" ", "")
    b = (best_name or "").replace(" ", "")
    if q and b:
        ed = Levenshtein.distance(q, b)
        if 1 <= ed <= 2 and best_score < 92:
            flags.append(f"Minor edit distance {ed} to a known brand")
        for a, c in [("0","o"),("o","0"),("1","l"),("l","1"),("i","l"),("rn","m")]:
            if a in q and q.replace(a, c) == b:
                flags.append(f"Character substitution pattern {a}->{c}")
                break
    return flags
