# Quick Start: TTS Integration

## 🎯 Objective
Integrate ElevenLabs Text-to-Speech so that bot replies are automatically spoken after processing `/ask` requests.

## ✅ What's Already Done

The TTS integration has been implemented with the following features:

### Backend (Gateway Service)
- ✅ `/tts` endpoint in gateway service
- ✅ ElevenLabs API integration with caching
- ✅ Audio file serving via `/static/audio/`
- ✅ Environment-driven configuration

### Frontend (React)
- ✅ Voice service with TTS function
- ✅ Audio player with autoplay policy handling
- ✅ Auto-speak toggle in chat interface
- ✅ Integration with main chat flow

### Infrastructure
- ✅ Docker compose configuration
- ✅ Environment variables setup
- ✅ Static file hosting

## 🚀 Quick Setup

### 1. Configure API Key
Update your `.env` file:
```env
ELEVENLABS_API_KEY=sk_your_api_key_here
ELEVENLABS_VOICE_ID=21m00Tcm4TlvDq8ikWAM
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

### 2. Update Frontend Environment
Update `intel-campus-ai-main/.env`:
```env
VITE_API_URL=http://your-domain:8000
VITE_VOICE_BASE_URL=http://your-domain:8000
```

### 3. Start Services
```bash
# Using Docker Compose
docker-compose up --build

# Or manual development
cd services/gateway && uvicorn app:app --reload
cd intel-campus-ai-main && npm run dev
```

### 4. Test Integration
```bash
# Test TTS endpoint
curl -X POST http://localhost:8000/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Xin chào! Tôi là trợ lý ảo Campus Helpdesk."}'

# Run automated tests
python test_tts_integration.py
```

## 🎛️ How It Works

### 1. Chat Flow with Auto-TTS
```
User sends message → /ask endpoint → Bot generates reply → Auto-call /tts → Audio plays
```

### 2. Frontend Integration
- `useChat` hook automatically calls TTS after bot reply
- User can toggle auto-speak with "Voice On/Off" button
- AudioPlayer handles browser autoplay policies
- Settings persist in localStorage

### 3. Backend Processing
- `/tts` endpoint receives text from frontend
- Calls ElevenLabs API with configured voice/model
- Caches audio files to save credits
- Returns audio URL for client playback

## 🔧 Configuration Options

### Voice Settings
```typescript
// Frontend: Customize TTS parameters
await tts("Hello world", {
  voice_id: "different_voice_id",
  model_id: "eleven_turbo_v2",    // Faster
  stability: 0.8,                 // Voice stability
  similarity_boost: 0.6          // Voice similarity
});
```

### Backend Caching
```python
# Audio files cached by content hash
# Same text = reused cached file
# Saves ElevenLabs API credits
```

## 🐛 Troubleshooting

### Common Issues:

**TTS not working:**
1. Check `ELEVENLABS_API_KEY` is valid
2. Verify API quota available
3. Check network connectivity
4. Ensure audio permissions in browser

**Audio not playing:**
1. Click anywhere on page first (browser policy)
2. Check "Voice On" toggle is active
3. Try different browser (Chrome recommended)
4. Check browser console for errors

**Slow response:**
1. Use `eleven_turbo_v2` for faster generation
2. Verify caching is working (2nd request should be instant)
3. Check ElevenLabs API latency

## 📋 API Reference

### POST /tts
**Request:**
```json
{
  "text": "Text to convert",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "model_id": "eleven_multilingual_v2",
  "stability": 0.7,
  "similarity_boost": 0.7
}
```

**Response:**
```json
{
  "text": "Text to convert",
  "audio_url": "/static/audio/abc123.mp3",
  "cached": false
}
```

## 🎉 Next Steps

### Possible Extensions:
1. **Streaming TTS**: Implement `/tts/stream` for lower latency
2. **Voice Selection**: Add UI for users to choose different voices
3. **Speech-to-Text**: Add microphone input for voice questions
4. **Voice Commands**: Add voice-activated shortcuts
5. **Multi-language**: Extend to other languages

### Production Considerations:
1. **Rate Limiting**: Protect against TTS abuse
2. **Audio Cleanup**: Manage storage space for cached files
3. **CDN Integration**: Use CDN for audio file delivery
4. **Monitoring**: Track TTS usage and errors
5. **Fallback**: Graceful degradation when TTS fails

---

For detailed setup and troubleshooting, see: [VOICE_CHAT_SETUP.md](VOICE_CHAT_SETUP.md)
