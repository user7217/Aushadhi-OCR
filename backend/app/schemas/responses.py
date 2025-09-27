from pydantic import BaseModel
from typing import Optional, List

class Match(BaseModel):
    name: str
    score: float
    row_index: int
    generic: Optional[str] = None
    manufacturer: Optional[str] = None
    form: Optional[str] = None          # include in model
    alias_name: Optional[str] = None
    main_uses: Optional[str] = None     # include in model

class InferenceResponse(BaseModel):
    ocr_text: str
    top_k: List[Match]
    mismatch_flag: bool
    flags: List[str]
    main_uses: Optional[str] = ""       # top match’s uses for convenience
