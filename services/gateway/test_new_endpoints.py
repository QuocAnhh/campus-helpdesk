"""
Tests for the new endpoints: /me, /me/tickets, and /sessions/{session_id}/history
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import json
import time

# Mock Redis and httpx for testing
@pytest.fixture
def mock_redis():
    return Mock()

@pytest.fixture
def mock_httpx():
    return AsyncMock()

@pytest.fixture
def client():
    """Create test client with mocked dependencies"""
    # Import here to avoid import issues during test discovery
    from app import app
    return TestClient(app)

class TestMeEndpoint:
    """Tests for GET /me endpoint"""
    
    def test_me_with_jwt_token(self, client):
        """Test /me endpoint with valid JWT token"""
        # Mock JWT token that would contain student_id
        token = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJzdHVkZW50MTIzIiwiZXhwIjoxNjQwOTk1MjAwfQ.example"
        
        with patch('app.extract_student_id_from_jwt', return_value="student123"):
            response = client.get("/me", headers={"Authorization": token})
            
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == "student123"
        assert data["name"] == "Unknown"
        assert data["major"] == "Unknown"
    
    def test_me_with_student_id_header(self, client):
        """Test /me endpoint with x-student-id header (dev fallback)"""
        response = client.get("/me", headers={"x-student-id": "student456"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["student_id"] == "student456"
        assert data["name"] == "Unknown"
        assert data["major"] == "Unknown"
    
    def test_me_without_auth(self, client):
        """Test /me endpoint without authentication"""
        response = client.get("/me")
        
        assert response.status_code == 401
        assert "Student ID not found" in response.json()["detail"]

class TestMyTicketsEndpoint:
    """Tests for GET /me/tickets endpoint"""
    
    def test_my_tickets_success(self, client):
        """Test /me/tickets endpoint with successful response"""
        mock_tickets_response = {
            "tickets": [
                {
                    "id": 1,
                    "subject": "Test Ticket",
                    "category": "technical",
                    "priority": "medium",
                    "status": "open",
                    "created_at": "2023-01-01T00:00:00Z"
                }
            ]
        }
        
        with patch('app.get_student_id', return_value="student123"), \
             patch.object(client.app.state, 'http_client') as mock_client:
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_tickets_response
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = client.get("/me/tickets")
            
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["subject"] == "Test Ticket"
    
    def test_my_tickets_empty_response(self, client):
        """Test /me/tickets endpoint with empty response"""
        with patch('app.get_student_id', return_value="student123"), \
             patch.object(client.app.state, 'http_client') as mock_client:
            
            mock_response = Mock()
            mock_response.status_code = 404
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = client.get("/me/tickets")
            
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_my_tickets_without_auth(self, client):
        """Test /me/tickets endpoint without authentication"""
        with patch('app.get_student_id', return_value=None):
            response = client.get("/me/tickets")
            
        assert response.status_code == 401
        assert "Student ID not found" in response.json()["detail"]
    
    def test_my_tickets_service_error(self, client):
        """Test /me/tickets endpoint when ticket service returns error"""
        with patch('app.get_student_id', return_value="student123"), \
             patch.object(client.app.state, 'http_client') as mock_client:
            
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_client.get = AsyncMock(return_value=mock_response)
            
            response = client.get("/me/tickets")
            
        assert response.status_code == 500

class TestSessionHistoryEndpoint:
    """Tests for GET /sessions/{session_id}/history endpoint"""
    
    def test_session_history_success(self, client):
        """Test session history endpoint with successful response"""
        mock_history = [
            {
                "user": "Hello",
                "bot": "Hi there!",
                "timestamp": time.time(),
                "agent": "greeting",
                "student_id": "student123"
            }
        ]
        
        with patch('app.get_student_id', return_value="student123"), \
             patch('app.get_chat_history', return_value=mock_history):
            
            response = client.get("/sessions/test-session-123/history")
            
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user"] == "Hello"
        assert data[0]["bot"] == "Hi there!"
        assert data[0]["agent"] == "greeting"
    
    def test_session_history_filtered_by_student(self, client):
        """Test session history filters messages by student_id"""
        mock_history = [
            {
                "user": "Hello from student123",
                "bot": "Hi student123!",
                "timestamp": time.time(),
                "agent": "greeting",
                "student_id": "student123"
            },
            {
                "user": "Hello from student456", 
                "bot": "Hi student456!",
                "timestamp": time.time(),
                "agent": "greeting",
                "student_id": "student456"
            }
        ]
        
        with patch('app.get_student_id', return_value="student123"), \
             patch('app.get_chat_history', return_value=mock_history):
            
            response = client.get("/sessions/test-session-123/history")
            
        assert response.status_code == 200
        data = response.json()
        # Should only return messages for student123
        assert len(data) == 1
        assert data[0]["student_id"] == "student123"
    
    def test_session_history_without_auth(self, client):
        """Test session history endpoint without authentication"""
        with patch('app.get_student_id', return_value=None):
            response = client.get("/sessions/test-session-123/history")
            
        assert response.status_code == 401
        assert "Student ID not found" in response.json()["detail"]
    
    def test_session_history_empty(self, client):
        """Test session history endpoint with empty history"""
        with patch('app.get_student_id', return_value="student123"), \
             patch('app.get_chat_history', return_value=[]):
            
            response = client.get("/sessions/test-session-123/history")
            
        assert response.status_code == 200
        data = response.json()
        assert data == []

if __name__ == "__main__":
    pytest.main([__file__])
