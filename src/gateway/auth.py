from google import genai

from .config import Config

_client: genai.Client | None = None


def get_client(config: Config) -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(
            vertexai=True,
            project=config.project,
            location=config.location,
        )
    return _client
