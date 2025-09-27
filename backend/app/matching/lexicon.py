from typing import Set
import re

WORD_RE = re.compile(r"[a-z]+(?:\d+)?%?")

def build_lexicons(df) -> dict[str, Set[str]]:
    brands = set()
    actives = set()
    for row in df.itertuples():
        for token in WORD_RE.findall(str(getattr(row, "product_name", "")).lower()):
            brands.add(token)
        for token in WORD_RE.findall(str(getattr(row, "strength", "")).lower()):
            actives.add(token)
    return {"brands": brands, "actives": actives}
