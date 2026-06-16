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


def _fake_cache(name="cachedContents/abc123"):
    cc = MagicMock()
    cc.name = name
    cc.model = "models/gemini-2.5-flash"
    cc.display_name = "my-cache"
    cc.create_time = None
    cc.update_time = None
    cc.expire_time = None
    cc.usage_metadata = MagicMock(total_token_count=42)
    return cc


def test_create_cached_content(client):
    mock_client = MagicMock()
    mock_client.aio.caches.create = AsyncMock(return_value=_fake_cache())

    with patch("gateway.auth._client", mock_client):
        response = client.post(
            "/v1beta/cachedContents",
            json={
                "model": "models/gemini-2.5-flash",
                "contents": [{"parts": [{"text": "cache me"}]}],
                "ttl": "3600s",
                "displayName": "my-cache",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "cachedContents/abc123"
    assert data["usageMetadata"]["totalTokenCount"] == 42

    _, kwargs = mock_client.aio.caches.create.call_args
    assert kwargs["model"] == "models/gemini-2.5-flash"
    assert kwargs["config"].ttl == "3600s"
    assert kwargs["config"].display_name == "my-cache"


def test_get_cached_content(client):
    mock_client = MagicMock()
    mock_client.aio.caches.get = AsyncMock(return_value=_fake_cache())

    with patch("gateway.auth._client", mock_client):
        response = client.get("/v1beta/cachedContents/abc123")

    assert response.status_code == 200
    assert response.json()["name"] == "cachedContents/abc123"
    _, kwargs = mock_client.aio.caches.get.call_args
    assert kwargs["name"] == "cachedContents/abc123"


def test_list_cached_contents(client):
    pager = MagicMock()
    pager.page = [_fake_cache("cachedContents/a"), _fake_cache("cachedContents/b")]
    pager.config = {"page_token": "next-tok"}

    mock_client = MagicMock()
    mock_client.aio.caches.list = AsyncMock(return_value=pager)

    with patch("gateway.auth._client", mock_client):
        response = client.get("/v1beta/cachedContents?pageSize=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["cachedContents"]) == 2
    assert data["nextPageToken"] == "next-tok"
    _, kwargs = mock_client.aio.caches.list.call_args
    assert kwargs["config"]["page_size"] == 2


def test_update_cached_content(client):
    mock_client = MagicMock()
    mock_client.aio.caches.update = AsyncMock(return_value=_fake_cache())

    with patch("gateway.auth._client", mock_client):
        response = client.patch(
            "/v1beta/cachedContents/abc123",
            json={"ttl": "7200s"},
        )

    assert response.status_code == 200
    _, kwargs = mock_client.aio.caches.update.call_args
    assert kwargs["name"] == "cachedContents/abc123"
    assert kwargs["config"].ttl == "7200s"


def test_delete_cached_content(client):
    mock_client = MagicMock()
    mock_client.aio.caches.delete = AsyncMock(return_value=MagicMock())

    with patch("gateway.auth._client", mock_client):
        response = client.delete("/v1beta/cachedContents/abc123")

    assert response.status_code == 200
    assert response.json() == {}
    _, kwargs = mock_client.aio.caches.delete.call_args
    assert kwargs["name"] == "cachedContents/abc123"
