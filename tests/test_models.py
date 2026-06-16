import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "test-project")
    os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")
    from gateway.main import app
    with TestClient(app) as c:
        yield c


def test_list_models(client):
    response = client.get("/v1beta/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    names = [m["name"] for m in data["models"]]
    assert "models/gemini-2.5-pro" in names
    assert "models/gemini-2.5-flash" in names
