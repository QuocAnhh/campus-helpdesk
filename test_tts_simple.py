#!/usr/bin/env python3
"""
Simple TTS integration test using curl commands
"""

import os
import subprocess
import json

def run_curl(url, method="GET", data=None, headers=None):
    """Run curl command and return result"""
    cmd = ["curl", "-s"]
    
    if method == "POST":
        cmd.append("-X POST")
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    if data:
        cmd.extend(["-d", json.dumps(data)])
    
    cmd.append(url)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Timeout"
    except Exception as e:
        return False, "", str(e)

def test_gateway_health():
    """Test gateway health"""
    print("🏥 Testing Gateway health...")
    success, stdout, stderr = run_curl("http://localhost:8000/health")
    
    if success and stdout:
        try:
            data = json.loads(stdout)
            print("✅ Gateway is healthy!")
            print(f"   - Status: {data.get('status', 'unknown')}")
            print(f"   - Available agents: {len(data.get('available_agents', []))}")
            return True
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {stdout[:100]}")
            return False
    else:
        print(f"❌ Gateway health check failed")
        if stderr:
            print(f"   Error: {stderr}")
        return False

def test_tts_endpoint():
    """Test TTS endpoint"""
    print("🎤 Testing TTS endpoint...")
    
    test_text = "Xin chào! Tôi là trợ lý ảo Campus Helpdesk."
    data = {"text": test_text}
    headers = {"Content-Type": "application/json"}
    
    success, stdout, stderr = run_curl(
        "http://localhost:8000/tts", 
        method="POST", 
        data=data, 
        headers=headers
    )
    
    if success and stdout:
        try:
            result = json.loads(stdout)
            print("✅ TTS endpoint successful!")
            print(f"   - Text: {result['text'][:50]}...")
            print(f"   - Audio URL: {result['audio_url']}")
            print(f"   - Cached: {result['cached']}")
            return True
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response: {stdout[:100]}")
            return False
    else:
        print(f"❌ TTS endpoint failed")
        if stderr:
            print(f"   Error: {stderr}")
        return False

def check_environment():
    """Check environment configuration"""
    print("🔧 Checking environment configuration...")
    
    # Check .env file exists
    env_file = ".env"
    if os.path.exists(env_file):
        print("✅ .env file found")
        
        # Read key variables
        with open(env_file, 'r') as f:
            content = f.read()
            
        if "ELEVENLABS_API_KEY=" in content and not "your_elevenlabs_api_key_here" in content:
            print("✅ ELEVENLABS_API_KEY configured")
        else:
            print("❌ ELEVENLABS_API_KEY not properly configured")
            
        if "ELEVENLABS_VOICE_ID=" in content:
            print("✅ ELEVENLABS_VOICE_ID configured")
        else:
            print("❌ ELEVENLABS_VOICE_ID not configured")
            
    else:
        print("❌ .env file not found")
        return False
    
    # Check frontend .env
    frontend_env = "intel-campus-ai-main/.env"
    if os.path.exists(frontend_env):
        print("✅ Frontend .env file found")
    else:
        print("⚠️  Frontend .env file not found")
    
    return True

def main():
    """Run all tests"""
    print("🧪 Campus Helpdesk TTS Integration Test")
    print("=" * 50)
    
    # Check environment first
    if not check_environment():
        print("\n❌ Environment configuration issues found")
        print("Please check your .env configuration")
        return
    
    print()
    
    # Test sequence
    tests = [
        ("Gateway Health", test_gateway_health),
        ("TTS Endpoint", test_tts_endpoint),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! TTS integration is ready.")
    else:
        print("⚠️  Some tests failed. Make sure services are running:")
        print("   docker-compose up --build")
        print("   OR")
        print("   cd services/gateway && uvicorn app:app --reload")

if __name__ == "__main__":
    main()
