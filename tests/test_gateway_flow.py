import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
import os

# Add service to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'gateway')))
from app import app

client = TestClient(app)

@patch('httpx.AsyncClient.post')
def test_ask_flow_no_llm(mock_post):
    # Mock responses from downstream services
    mock_post.side_effect = [
        # router
        MagicMock(status_code=200, json=lambda: {"label": "it.reset_password", "confidence": 0.9, "entities": {}}),
        # policy
        MagicMock(status_code=200, json=lambda: {"citations": [], "needs_answer": False}),
        # answer
        MagicMock(status_code=200, json=lambda: {"reply": "...", "citations": [], "suggested_tool_call": None}),
        # ticket
        MagicMock(status_code=200, json=lambda: {"ok": True})
    ]

    response = client.post("/ask", params={"use_llm": False}, json={"channel": "web", "text": "reset password"})
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert "answer" in data 