import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data

def test_tickets_endpoint():
    response = client.get("/tickets")
    assert response.status_code == 200
    data = response.json()
    assert "tickets" in data
    assert isinstance(data["tickets"], list)

def test_query_endpoint():
    payload = {"question": "What is the liveness probe timeout?", "top_k": 3}
    response = client.post("/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data

def test_ticket_approval_endpoint():
    response = client.post("/tickets/tkt_1001/approve?custom_response=Approved%20by%20agent")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
    assert data["ticket_id"] == "tkt_1001"

def test_ticket_escalation_endpoint():
    response = client.post("/tickets/tkt_1002/escalate?reason=Tier%202%20review")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "escalated"

def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "fcr_rate" in data
    assert "avg_response_time" in data
