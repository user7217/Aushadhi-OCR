import cv2
import numpy as np
from PIL import Image

def pil_to_cv(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def cv_to_pil(arr: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))

def preprocess_for_ocr(pil_img: Image.Image, min_height: int = 900, enable_threshold: bool = False) -> Image.Image:
    """
    Conservative preprocessing:
    - grayscale
    - light median blur
    - optional upscale to min height
    - optional adaptive threshold for very uneven lighting
    """
    img = pil_to_cv(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    den = cv2.medianBlur(gray, 3)

    h, w = den.shape[:2]
    out = den
    if h < min_height:
        scale = min_height / float(h)
        out = cv2.resize(out, (int(w * scale), min_height), interpolation=cv2.INTER_CUBIC)

    if enable_threshold:
        # Use adaptive when lighting is uneven; keep it optional
        out = cv2.adaptiveThreshold(
            out, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            21, 10
        )

    # Return 3-channel for OCR backends expecting color
    out3 = cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)
    return cv_to_pil(out3)
