#!/usr/bin/env python3
"""
Simple TTS integration test for Docker deployment
Uses urllib instead of httpx for better compatibility
"""

import json
import urllib.request
import urllib.parse
import urllib.error

# Configuration for production server
GATEWAY_URL = "http://54.252.240.140:8000"
TEST_TEXT = "Xin chào! Tôi là trợ lý ảo của Campus Helpdesk. Tôi có thể giúp bạn với các câu hỏi về học tập."

def test_gateway_health():
    """Test gateway health endpoint"""
    print("🏥 Testing Gateway health...")
    
    try:
        with urllib.request.urlopen(f"{GATEWAY_URL}/health", timeout=10) as response:
            if response.status == 200:
                result = json.loads(response.read().decode())
                print("✅ Gateway is healthy!")
                print(f"   - Status: {result.get('status', 'unknown')}")
                print(f"   - Available agents: {len(result.get('available_agents', []))}")
                return True
            else:
                print(f"❌ Gateway health check failed: {response.status}")
                return False
    except Exception as e:
        print(f"❌ Gateway health error: {e}")
        return False

def test_tts_endpoint():
    """Test TTS endpoint"""
    print("🎤 Testing TTS endpoint...")
    
    # Prepare request data
    data = {
        "text": TEST_TEXT,
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "model_id": "eleven_multilingual_v2"
    }
    
    # Encode JSON data
    json_data = json.dumps(data).encode('utf-8')
    
    # Create request
    req = urllib.request.Request(
        f"{GATEWAY_URL}/tts",
        data=json_data,
        headers={
            'Content-Type': 'application/json',
            'Content-Length': len(json_data)
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status == 200:
                result = json.loads(response.read().decode())
                print("✅ TTS endpoint successful!")
                print(f"   - Text: {result['text'][:50]}...")
                print(f"   - Audio URL: {result['audio_url']}")
                print(f"   - Cached: {result['cached']}")
                return result['audio_url']
            else:
                print(f"❌ TTS failed: {response.status}")
                return None
    except urllib.error.HTTPError as e:
        print(f"❌ TTS HTTP error: {e.code} - {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"   Error details: {error_body}")
        except:
            pass
        return None
    except Exception as e:
        print(f"❌ TTS error: {e}")
        return None

def test_chat_integration():
    """Test chat + TTS integration"""
    print("💬 Testing Chat + TTS integration...")
    
    # First send a chat message
    chat_data = {
        "text": "Chào bạn! Tôi muốn biết thông tin về học phí.",
        "channel": "web",
        "student_id": "test_user",
        "session_id": "test_session_123"
    }
    
    json_data = json.dumps(chat_data).encode('utf-8')
    
    req = urllib.request.Request(
        f"{GATEWAY_URL}/ask",
        data=json_data,
        headers={
            'Content-Type': 'application/json',
            'Content-Length': len(json_data)
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                result = json.loads(response.read().decode())
                bot_reply = result['answer']['reply']
                print("✅ Chat request successful!")
                print(f"   - Bot reply: {bot_reply[:100]}...")
                
                # Now test TTS with the bot reply
                tts_data = {"text": bot_reply}
                tts_json = json.dumps(tts_data).encode('utf-8')
                
                tts_req = urllib.request.Request(
                    f"{GATEWAY_URL}/tts",
                    data=tts_json,
                    headers={
                        'Content-Type': 'application/json',
                        'Content-Length': len(tts_json)
                    },
                    method='POST'
                )
                
                with urllib.request.urlopen(tts_req, timeout=60) as tts_response:
                    if tts_response.status == 200:
                        tts_result = json.loads(tts_response.read().decode())
                        print("✅ TTS integration successful!")
                        print(f"   - Audio URL: {tts_result['audio_url']}")
                        return True
                    else:
                        print(f"❌ TTS integration failed: {tts_response.status}")
                        return False
            else:
                print(f"❌ Chat request failed: {response.status}")
                return False
                
    except Exception as e:
        print(f"❌ Chat integration error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Campus Helpdesk TTS Integration Test (Docker)")
    print("=" * 60)
    print(f"🔗 Testing server: {GATEWAY_URL}")
    print()
    
    # Test sequence
    tests = [
        ("Gateway Health", test_gateway_health),
        ("TTS Endpoint", test_tts_endpoint),
        ("Chat + TTS Integration", test_chat_integration),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! TTS integration is working correctly.")
        print("\n💡 Frontend Usage:")
        print("   1. Open http://54.252.240.140:1610")
        print("   2. Login to chat page")
        print("   3. Look for 'Voice On/Off' toggle in header")
        print("   4. Send a message and hear auto TTS!")
    else:
        print("⚠️  Some tests failed. Check Docker containers:")
        print("   docker-compose ps")
        print("   docker-compose logs gateway")

if __name__ == "__main__":
    main()
