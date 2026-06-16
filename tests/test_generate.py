import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
    from gateway.main import app
    with TestClient(app) as c:
        yield c


def _fake_response():
    part = MagicMock()
    part.text = "Hello!"
    content = MagicMock()
    content.role = "model"
    content.parts = [part]
    candidate = MagicMock()
    candidate.content = content
    candidate.finish_reason = MagicMock()
    candidate.finish_reason.name = "STOP"
    response = MagicMock()
    response.candidates = [candidate]
    response.usage_metadata = None
    return response


def test_generate_content(client):
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=_fake_response())

    with patch("gateway.auth._client", mock_client):
        response = client.post(
            "/v1beta/models/gemini-2.5-flash:generateContent",
            json={"contents": [{"parts": [{"text": "Hello"}]}]},
        )

    assert response.status_code == 200
    data = response.json()
    assert "candidates" in data
    assert data["candidates"][0]["content"]["parts"][0]["text"] == "Hello!"
    assert data["candidates"][0]["finishReason"] == "STOP"
