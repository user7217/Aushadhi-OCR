import re
from typing import List
import pandas as pd
from rapidfuzz import fuzz, process
from pydantic import BaseModel

class Match(BaseModel):
    name: str
    score: float
    row_index: int
    generic: str | None = None
    manufacturer: str | None = None

def normalize_text(s: str) -> str:
    s = s.lower()
    s = s.replace("-", " ")
    s = re.sub(r"[^a-z0-9\s+]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _scorer(a: str, b: str, **kwargs) -> float:
    s1 = fuzz.token_set_ratio(a, b)
    s2 = fuzz.partial_ratio(a, b)
    return 0.6 * s1 + 0.4 * s2

def fuzzy_topk(query: str, df: pd.DataFrame, k: int = 5) -> List[Match]:
    candidates = []
    for idx, row in enumerate(df.itertuples()):
        combined_name = f"{row.product_name} {row.alias_name or ''}".strip()
        candidates.append((combined_name, idx))
    names = [c[0] for c in candidates]
    matches = process.extract(query, names, scorer=_scorer, limit=k)
    out: List[Match] = []
    for name, score, pos in matches:
        idx = candidates[pos][1]
        row = df.iloc[idx]
        out.append(Match(
            name=row.product_name,
            score=float(score),
            row_index=int(idx),
            generic=row.get("strength"),
            manufacturer=row.get("manufacturer")
        ))
    return out

def suspicious_tweaks(query: str, best_name: str, best_score: float) -> list[str]:
    from rapidfuzz.distance import Levenshtein
    flags: list[str] = []
    if best_score < 75:
        flags.append(f"Low similarity score {best_score:.1f}")
    q = query.replace(" ", "")
    b = best_name.replace(" ", "")
    if q and b:
        ed = Levenshtein.distance(q, b)
        if 1 <= ed <= 2 and best_score < 92:
            flags.append(f"Minor edit distance {ed} to a known brand")
        swaps = [("0","o"),("o","0"),("1","l"),("l","1"),("i","l"),("rn","m")]
        for a, c in swaps:
            if a in q and q.replace(a, c) == b:
                flags.append(f"Character substitution pattern {a}->{c}")
                break
    return flags
