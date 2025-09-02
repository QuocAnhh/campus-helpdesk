"""
Test voice chat functionality
"""

import asyncio
import httpx
import io
import json
from pathlib import Path

async def test_voice_chat_endpoint():
    """Test the voice chat endpoint with a mock audio file"""
    
    # Create a mock audio file (empty WebM for testing)
    mock_audio = b"mock_audio_data"
    
    files = {
        'audio_file': ('test.webm', io.BytesIO(mock_audio), 'audio/webm')
    }
    
    data = {
        'session_id': 'test-session-123'
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/voice-chat",
                files=files,
                data=data,
                timeout=30.0
            )
            
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Session ID: {result.get('session_id')}")
                print(f"Transcript: {result.get('transcript')}")
                print(f"Text: {result.get('text')}")
                print(f"Audio URL: {result.get('audio_url')}")
            
        except Exception as e:
            print(f"Error: {e}")

async def test_health_check():
    """Test if the gateway is running"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/health")
            print(f"Health check: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Health check failed: {e}")

if __name__ == "__main__":
    print("Testing Voice Chat API...")
    asyncio.run(test_health_check())
    asyncio.run(test_voice_chat_endpoint())
