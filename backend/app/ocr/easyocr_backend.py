from PIL import Image
import numpy as np
from ..deps import get_easyocr_reader

def easyocr_run(img: Image.Image) -> str:
    reader = get_easyocr_reader()
    arr = np.array(img.convert("L"))
    lines = reader.readtext(arr, detail=0, paragraph=True)
    return " ".join(lines).strip()
