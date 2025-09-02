#!/usr/bin/env python3
"""
Test script for TTS integration in Campus Helpdesk
Tests both the gateway TTS endpoint and voice service
"""

import asyncio
import httpx
import json
import os
from pathlib import Path

# Configuration
GATEWAY_URL = "http://localhost:8000"
VOICE_URL = "http://localhost:8001"
TEST_TEXT = "Xin chào! Tôi là trợ lý ảo của Campus Helpdesk. Tôi có thể giúp bạn với các câu hỏi về học tập và sinh hoạt tại trường."

async def test_gateway_tts():
    """Test TTS endpoint through gateway service"""
    print("🎯 Testing Gateway TTS endpoint...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{GATEWAY_URL}/tts",
                json={
                    "text": TEST_TEXT,
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "model_id": "eleven_multilingual_v2"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Gateway TTS endpoint successful!")
                print(f"   - Text: {result['text'][:50]}...")
                print(f"   - Audio URL: {result['audio_url']}")
                print(f"   - Cached: {result['cached']}")
                return result['audio_url']
            else:
                print(f"❌ Gateway TTS failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Gateway TTS error: {e}")
            return None

async def test_voice_service_health():
    """Test voice service health endpoint"""
    print("🏥 Testing Voice service health...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{VOICE_URL}/health")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Voice service is healthy!")
                print(f"   - Service: {result['service']}")
                print(f"   - API Key configured: {result['api_key_configured']}")
                print(f"   - Voice ID: {result['voice_id']}")
                return True
            else:
                print(f"❌ Voice service health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Voice service health error: {e}")
            return False

async def test_voice_service_tts():
    """Test TTS endpoint in voice service directly"""
    print("🎤 Testing Voice service TTS endpoint...")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{VOICE_URL}/tts",
                json={
                    "text": TEST_TEXT,
                    "voice_id": "21m00Tcm4TlvDq8ikWAM",
                    "model_id": "eleven_multilingual_v2"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Voice service TTS successful!")
                print(f"   - Text: {result['text'][:50]}...")
                print(f"   - Audio URL: {result['audio_url']}")
                print(f"   - Cached: {result['cached']}")
                return result['audio_url']
            else:
                print(f"❌ Voice service TTS failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Voice service TTS error: {e}")
            return None

async def test_gateway_health():
    """Test gateway health endpoint"""
    print("🏥 Testing Gateway health...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{GATEWAY_URL}/health")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Gateway is healthy!")
                print(f"   - Status: {result['status']}")
                print(f"   - Available agents: {len(result['available_agents'])}")
                return True
            else:
                print(f"❌ Gateway health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Gateway health error: {e}")
            return False

async def test_chat_integration():
    """Test chat integration with auto TTS"""
    print("💬 Testing Chat + TTS integration...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Send a chat message
            response = await client.post(
                f"{GATEWAY_URL}/ask",
                json={
                    "text": "Chào bạn! Tôi cần hỗ trợ về thông tin học phí.",
                    "channel": "web",
                    "student_id": "test_user",
                    "session_id": "test_session_123"
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                bot_reply = result['answer']['reply']
                print("✅ Chat request successful!")
                print(f"   - Bot reply: {bot_reply[:100]}...")
                
                # Now test TTS with the bot reply
                tts_response = await client.post(
                    f"{GATEWAY_URL}/tts",
                    json={"text": bot_reply}
                )
                
                if tts_response.status_code == 200:
                    tts_result = tts_response.json()
                    print("✅ TTS integration successful!")
                    print(f"   - Audio URL: {tts_result['audio_url']}")
                    return True
                else:
                    print(f"❌ TTS integration failed: {tts_response.status_code}")
                    return False
                    
            else:
                print(f"❌ Chat request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Chat integration error: {e}")
            return False

async def main():
    """Run all tests"""
    print("🧪 Campus Helpdesk TTS Integration Test")
    print("=" * 50)
    
    # Check environment
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("❌ ELEVENLABS_API_KEY not found in environment")
        print("   Please set your ElevenLabs API key")
        return
    
    print(f"🔑 ElevenLabs API key configured: {os.getenv('ELEVENLABS_API_KEY', '')[:10]}...")
    print()
    
    # Test sequence
    tests = [
        ("Gateway Health", test_gateway_health),
        ("Voice Service Health", test_voice_service_health), 
        ("Voice Service TTS", test_voice_service_tts),
        ("Gateway TTS", test_gateway_tts),
        ("Chat + TTS Integration", test_chat_integration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        results[test_name] = await test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! TTS integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")

if __name__ == "__main__":
    # Load environment variables if .env file exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📁 Loaded environment variables from .env file")
    except ImportError:
        print("📁 python-dotenv not available, using system environment")
    
    asyncio.run(main())
