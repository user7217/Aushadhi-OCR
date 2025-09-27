from rapidfuzz.distance import Levenshtein

def correct_tokens(text: str, lex: set[str], max_ed: int = 1) -> str:
    tokens = text.split()
    out = []
    for t in tokens:
        # skip numbers-only tokens to avoid over-correction
        if t.isdigit():
            out.append(t); continue
        best = t
        best_d = 999
        # small optimization: only consider lex words with same first letter
        for w in lex:
            if w[0] != t[0]:
                continue
            d = Levenshtein.distance(t, w)
            if d < best_d and d <= max_ed:
                best, best_d = w, d
                if d == 0:
                    break
        out.append(best)
    return " ".join(out)
