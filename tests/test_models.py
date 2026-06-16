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


def _fake_model(name, **kwargs):
    m = MagicMock()
    m.name = name
    m.version = kwargs.get("version")
    m.display_name = kwargs.get("display_name")
    m.description = kwargs.get("description")
    m.input_token_limit = kwargs.get("input_token_limit")
    m.output_token_limit = kwargs.get("output_token_limit")
    m.supported_actions = kwargs.get("supported_actions")
    m.temperature = kwargs.get("temperature")
    m.max_temperature = kwargs.get("max_temperature")
    m.top_p = kwargs.get("top_p")
    m.top_k = kwargs.get("top_k")
    return m


def test_list_models(client):
    pager = MagicMock()
    pager.page = [
        _fake_model(
            "publishers/google/models/gemini-2.5-pro",
            display_name="Gemini 2.5 Pro",
            input_token_limit=1048576,
            output_token_limit=65536,
            supported_actions=["generateContent"],
        ),
        _fake_model("models/gemini-2.5-flash"),
    ]
    pager.config = {"page_token": "next-tok"}

    mock_client = MagicMock()
    mock_client.aio.models.list = AsyncMock(return_value=pager)

    with patch("gateway.auth._client", mock_client):
        response = client.get("/v1beta/models")

    assert response.status_code == 200
    data = response.json()
    names = [m["name"] for m in data["models"]]
    # Vertex publisher paths are normalized to the Gemini Developer API form.
    assert names == ["models/gemini-2.5-pro", "models/gemini-2.5-flash"]
    assert data["models"][0]["displayName"] == "Gemini 2.5 Pro"
    assert data["models"][0]["inputTokenLimit"] == 1048576
    assert data["models"][0]["supportedGenerationMethods"] == ["generateContent"]
    assert data["nextPageToken"] == "next-tok"


def test_list_models_pagination_params(client):
    pager = MagicMock()
    pager.page = []
    pager.config = {}

    mock_client = MagicMock()
    mock_client.aio.models.list = AsyncMock(return_value=pager)

    with patch("gateway.auth._client", mock_client):
        response = client.get("/v1beta/models?pageSize=5&pageToken=tok")

    assert response.status_code == 200
    _, kwargs = mock_client.aio.models.list.call_args
    assert kwargs["config"]["page_size"] == 5
    assert kwargs["config"]["page_token"] == "tok"
