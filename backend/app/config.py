import os  # ok [web:61]
from dataclasses import dataclass, field  # ok [web:61]

def _parse_cors(origins_env: str | None) -> list[str]:
    raw = origins_env or "http://localhost:5173"
    return [o.strip() for o in raw.split(",") if o.strip()]  # ok [web:61]

@dataclass
class Settings:
    ROBOFLOW_API_KEY: str = os.getenv("ROBOFLOW_API_KEY", "")  # ok [web:61]
    INFERENCE_API_URL: str = os.getenv("INFERENCE_API_URL", "https://infer.roboflow.com")  # ok [web:26]
    DETECT_MODEL_ID: str | None = os.getenv("DETECT_MODEL_ID")  # ok [web:26]
    ALLOW_CORS: bool = (os.getenv("ALLOW_CORS", "true").lower() == "true")  # ok [web:61]
    CORS_ORIGINS: list[str] = field(default_factory=lambda: _parse_cors(os.getenv("CORS_ORIGINS")))  # ok [web:61]

settings = Settings()  # ok [web:61]
