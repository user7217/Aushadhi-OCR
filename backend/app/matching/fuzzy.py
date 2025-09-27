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
    s = re.sub(r"[^a-z0-9\s+/;,+]", " ", s)  # keep + / ; , for splits
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _scorer(a: str, b: str, **kwargs) -> float:
    s1 = fuzz.token_set_ratio(a, b)
    s2 = fuzz.partial_ratio(a, b)
    return 0.6 * s1 + 0.4 * s2

def fuzzy_topk(query: str, df: pd.DataFrame, k: int = 5) -> List[Match]:
    query = normalize_text(query)
    candidates = []  # tuples (candidate_str, row_index, base_name)
    for idx, row in enumerate(df.itertuples()):
        product = row.product_name or ""
        strength = row.strength or ""
        # Split strength into aliases by delimiters ; + ,
        aliases = re.split(r"[;,+]", strength)
        aliases = [normalize_text(a) for a in aliases if a.strip()]
        # Include product_name (normalized) as well
        product_norm = normalize_text(product)
        # Candidate aliases + product_name - each linked to row idx and product base name
        for alias in aliases + [product_norm]:
            candidates.append((alias, idx, product))
    # Extract top matches by scoring against all aliases + product_name
    # process.extract returns list of (match_str, score, index) with index into candidates
    names = [c[0] for c in candidates]
    matches = process.extract(query, names, scorer=_scorer, limit=k*3)
    # Aggregate best by row_index, keep best score per uniq row to pick top-k rows
    best_per_row = {}
    for match_str, score, pos in matches:
        idx = candidates[pos][1]
        base_name = candidates[pos][2]
        if idx not in best_per_row or best_per_row[idx]["score"] < score:
            best_per_row[idx] = {"score": score, "name": base_name, "row_index": idx}
    # Sort aggregated best matches descending by score
    best_list = sorted(best_per_row.values(), key=lambda x: x["score"], reverse=True)[:k]

    out = []
    for best in best_list:
        row = df.iloc[best["row_index"]]
        out.append(Match(
            name=best["name"],
            score=float(best["score"]),
            row_index=best["row_index"],
            generic=row.get("strength"),
            manufacturer=row.get("manufacturer")
        ))
    return out

def suspicious_tweaks(query: str, best_name: str, best_score: float) -> List[str]:
    from rapidfuzz.distance import Levenshtein
    flags: List[str] = []
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
