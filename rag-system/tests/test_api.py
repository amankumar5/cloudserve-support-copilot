from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_api_health():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_api_drive_connect():
    res = client.post("/drive/connect", json={})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["connected", "sandbox_mode"]


def test_api_query():
    res = client.post("/query", json={"question": "What is the authentication protocol?"})
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "sources" in data
