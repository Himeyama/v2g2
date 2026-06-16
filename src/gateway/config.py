import os
from dataclasses import dataclass


@dataclass
class Config:
    project: str
    location: str
    host: str
    port: int
    log_level: str


def load_config() -> Config:
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT environment variable is required")

    location = os.environ.get("GOOGLE_CLOUD_LOCATION")
    if not location:
        raise RuntimeError("GOOGLE_CLOUD_LOCATION environment variable is required")

    return Config(
        project=project,
        location=location,
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "12080")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
