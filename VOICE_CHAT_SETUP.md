# Voice Chat Development Setup

## 🎯 Bước 1: Cấu hình API Keys

Cập nhật file `.env` trong thư mục gốc:

```env
# Voice Services - ElevenLabs TTS
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
PUBLIC_BASE_URL=http://54.252.240.140:8001

# Frontend API URLs  
VITE_API_URL=http://54.252.240.140:8000
```

Và cập nhật file `intel-campus-ai-main/.env`:

```env
VITE_API_URL=http://54.252.240.140:8000
VITE_VOICE_BASE_URL=http://54.252.240.140:8000
```

## 🚀 Bước 2: Chạy Services

### Option 1: Docker Compose (Recommended)
```bash
# Build và chạy tất cả services
docker-compose up --build

# Hoặc chạy specific services
docker-compose up --build gateway voice frontend
```

### Option 2: Development Mode

#### 1. Start Backend (Gateway với TTS)
```bash
cd services/gateway
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Start Voice Service (Optional - nếu muốn service riêng)
```bash
cd services/voice  
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8001 --reload
```

#### 3. Start Frontend
```bash
cd intel-campus-ai-main
npm install
npm run dev
```
uvicorn app:app --reload --port 8000
```

## 🧪 Bước 3: Test TTS Integration

### Automated Testing
```bash
# Chạy test script để kiểm tra tất cả endpoints
python test_tts_integration.py
```

### Manual Testing

1. **Open Browser**: http://localhost:5173 (hoặc production URL)
2. **Login**: Sử dụng credentials để đăng nhập  
3. **Chat Page**: Navigate to main chat
4. **Voice Toggle**: Thấy nút "Voice On/Off" trong header
5. **Test Auto-TTS**:
   - Đảm bảo "Voice On" đang active
   - Gửi tin nhắn: "Xin chào"
   - Bot reply sẽ tự động phát âm thanh
   - Click "Voice Off" để tắt auto-speak

### Direct API Testing

```bash
# Test TTS endpoint
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Xin chào! Tôi là trợ lý ảo Campus Helpdesk."}'

# Response format:
{
  "text": "Xin chào! Tôi là trợ lý ảo Campus Helpdesk.",
  "audio_url": "/static/audio/abc123.mp3", 
  "cached": false
}
```

## 🎛️ Features

### Auto-Speak Functionality
- ✅ **Auto-play TTS**: Bot replies tự động phát âm thanh
- ✅ **Voice Toggle**: User có thể bật/tắt trong giao diện
- ✅ **Browser Policy Handling**: Tự động xử lý autoplay restrictions
- ✅ **Preference Persistence**: Lưu setting trong localStorage

### TTS Configuration  
- ✅ **Multi-language**: Hỗ trợ tiếng Việt qua eleven_multilingual_v2
- ✅ **Voice Selection**: Có thể override voice_id trong request
- ✅ **Audio Caching**: Cache theo content để tiết kiệm credit
- ✅ **Quality Settings**: Configurable stability/similarity_boost

### Performance
- ✅ **Caching**: Same text → reuse cached audio file
- ✅ **Async Processing**: Non-blocking TTS generation  
- ✅ **Error Handling**: Graceful degradation if TTS fails
- ✅ **Timeout Protection**: 60s timeout for TTS requests

## 🔧 Configuration Options

### Environment Variables (.env)
```env
# Required
ELEVENLABS_API_KEY=sk_your_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM   # Default voice
ELEVENLABS_MODEL_ID=eleven_multilingual_v2  # For Vietnamese support

# Optional  
PUBLIC_BASE_URL=http://your-domain.com:8001  # For audio URLs
STATIC_AUDIO_DIR=/tmp/static/audio           # Audio storage path
```

### Frontend Environment (intel-campus-ai-main/.env)
```env
VITE_API_URL=http://your-api-domain:8000
VITE_VOICE_BASE_URL=http://your-api-domain:8000  # Points to gateway TTS
```

### Runtime TTS Parameters
```typescript
// Có thể customize trong frontend call
await tts("Hello world", {
  voice_id: "different_voice_id",
  model_id: "eleven_turbo_v2",        // Faster but lower quality
  stability: 0.8,                     // Voice stability (0-1)
  similarity_boost: 0.6,              // Voice similarity (0-1)  
  format: "mp3"                       // Audio format
});
```

## 🐛 Troubleshooting

### Common Issues:

1. **"Voice services not available"**
   - ✅ Check `ELEVENLABS_API_KEY` in .env
   - ✅ Restart gateway service
   - ✅ Verify API key has TTS quota

2. **Audio not playing**  
   - ✅ Click anywhere first (browser autoplay policy)
   - ✅ Check "Voice On" toggle is enabled
   - ✅ Check browser console for errors
   - ✅ Try different browser (Chrome recommended)

3. **TTS endpoint errors**
   - ✅ Check network connectivity to ElevenLabs API
   - ✅ Verify API key permissions and quota
   - ✅ Check audio storage directory permissions
   - ✅ Monitor gateway logs: `docker logs campus-helpdesk-gateway-1`

4. **Slow TTS response**
   - ✅ Use `eleven_turbo_v2` model for faster generation
   - ✅ Reduce text length for bot replies
   - ✅ Check network latency to ElevenLabs
   - ✅ Verify caching is working (2nd request should be instant)

### Debug Commands:

```bash
# Test gateway health + voice config
curl http://localhost:8000/health

# Test TTS endpoint directly
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Test message"}'

# Check TTS audio file generation
ls -la /tmp/static/audio/

# View gateway logs
docker logs campus-helpdesk-gateway-1 -f

# View voice service logs (if separate service)
docker logs campus-helpdesk-voice-1 -f

# Frontend dev server logs  
cd intel-campus-ai-main && npm run dev
```

## 🚀 Production Deployment

### Docker Compose Production:
```bash
# Build và deploy
docker-compose up -d --build

# Check services
docker-compose ps
docker-compose logs gateway
docker-compose logs voice
```

### Service URLs:
- **Frontend**: http://your-domain:1610
- **Gateway API**: http://your-domain:8000  
- **Voice Service**: http://your-domain:8001 (optional separate service)
- **TTS Endpoint**: http://your-domain:8000/tts

### Performance Tuning:
1. **Set appropriate PUBLIC_BASE_URL** for audio file serving
2. **Configure audio caching directory** with sufficient storage
3. **Monitor ElevenLabs API usage** and set quotas
4. **Use CDN** for static audio files in production
5. **Set up audio file cleanup** to manage storage space

## 🎯 API Reference

### POST /tts
Convert text to speech using ElevenLabs

**Request:**
```json
{
  "text": "Text to convert to speech",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",     // Optional
  "model_id": "eleven_multilingual_v2",   // Optional  
  "stability": 0.7,                       // Optional (0-1)
  "similarity_boost": 0.7,                // Optional (0-1)
  "format": "mp3"                         // Optional
}
```

**Response:**
```json
{
  "text": "Text to convert to speech",
  "audio_url": "/static/audio/hash123.mp3",
  "cached": false
}
```

### GET /health
Check service health including voice services

**Response:**
```json
{
  "status": "healthy",
  "available_agents": ["router", "faq", "technical"],
  "total_agents": 3
}
```

## Performance Tips

1. **Audio Quality**: 16kHz sample rate cho tốt nhất
2. **File Size**: Giới hạn 10MB per request
3. **Processing Time**: 2-5 giây cho STT + TTS
4. **Concurrent Users**: Max 10 voice processing đồng thời
