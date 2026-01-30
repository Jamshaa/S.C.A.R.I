
from fastapi.testclient import TestClient
from src.api.app import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"

def test_get_models():
    response = client.get("/models")
    assert response.status_code == 200
    assert "models" in response.json()
