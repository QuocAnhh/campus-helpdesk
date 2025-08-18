import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add service to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'router')))
from app import app

client = TestClient(app)

def test_classify_llm_stub():
    response = client.post("/classify_llm", json={"channel": "web", "text": "reset password"})
    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "it.reset_password"
    assert data["confidence"] == 0.9 