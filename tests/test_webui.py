from fastapi.testclient import TestClient
from harness.webui.app import create_app

def test_create_session():
    app = create_app()
    client = TestClient(app)
    response = client.post("/api/sessions", json={"task": "test task"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["status"] in ["running", "completed", "stopped"]

def test_get_session():
    app = create_app()
    client = TestClient(app)
    create_resp = client.post("/api/sessions", json={"task": "test"})
    sid = create_resp.json()["id"]
    response = client.get(f"/api/sessions/{sid}")
    assert response.status_code == 200
    assert response.json()["id"] == sid

def test_get_nonexistent_session_404():
    app = create_app()
    client = TestClient(app)
    response = client.get("/api/sessions/nonexistent")
    assert response.status_code == 404

def test_stop_session():
    app = create_app()
    client = TestClient(app)
    create_resp = client.post("/api/sessions", json={"task": "test"})
    sid = create_resp.json()["id"]
    response = client.post(f"/api/sessions/{sid}/stop")
    assert response.status_code == 200

def test_approve_without_pending_returns_409():
    app = create_app()
    client = TestClient(app)
    create_resp = client.post("/api/sessions", json={"task": "test"})
    sid = create_resp.json()["id"]
    response = client.post(f"/api/sessions/{sid}/approve")
    assert response.status_code == 409

def test_deny_without_pending_returns_409():
    app = create_app()
    client = TestClient(app)
    create_resp = client.post("/api/sessions", json={"task": "test"})
    sid = create_resp.json()["id"]
    response = client.post(f"/api/sessions/{sid}/deny", json={"reason": "no"})
    assert response.status_code == 409
