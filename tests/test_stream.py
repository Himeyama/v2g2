import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
    from gateway.main import app
    with TestClient(app) as c:
        yield c


def _fake_chunk(text: str):
    part = MagicMock()
    part.text = text
    content = MagicMock()
    content.role = "model"
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    candidate.finish_reason = None
    chunk = MagicMock()
    chunk.candidates = [candidate]
    chunk.usage_metadata = None
    return chunk


async def _fake_stream(*args, **kwargs):
    for text in ["Hello", " World"]:
        yield _fake_chunk(text)


def test_stream_generate_content(client):
    mock_client = MagicMock()
    mock_client.aio.models.generate_content_stream = _fake_stream

    with patch("gateway.auth._client", mock_client):
        response = client.post(
            "/v1beta/models/gemini-2.5-flash:streamGenerateContent",
            json={"contents": [{"parts": [{"text": "Hello"}]}]},
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]

    lines = [line for line in response.text.split("\n") if line.startswith("data: ")]
    assert lines[-1] == "data: [DONE]"

    first_chunk = json.loads(lines[0][len("data: "):])
    assert "candidates" in first_chunk
