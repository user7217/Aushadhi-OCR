from functools import lru_cache
from inference_sdk import InferenceHTTPClient, InferenceConfiguration
from .config import settings

@lru_cache(maxsize=1)
def get_inference_client():
    if not settings.ROBOFLOW_API_KEY:
        return None
    return InferenceHTTPClient(
        api_url=settings.INFERENCE_API_URL,
        api_key=settings.ROBOFLOW_API_KEY,
        inference_configuration=InferenceConfiguration(
            max_concurrent_requests=4,
            max_batch_size=1
        )
    )

_easy_reader = None
def get_easyocr_reader():
    global _easy_reader
    if _easy_reader is None:
        import easyocr
        _easy_reader = easyocr.Reader(['en'])
    return _easy_reader
