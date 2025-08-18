import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add service to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'policy')))
from app import app

client = TestClient(app)

def test_check_rag_empty():
    response = client.post("/check", json={"intent": {"label": "general.faq"}, "text": "some random query"})
    assert response.status_code == 200
    data = response.json()
    assert data["citations"] == []
    assert data["needs_answer"] is False 