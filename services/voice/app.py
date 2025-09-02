from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
import time
import hashlib
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Campus Voice Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False, 
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Setup static directories
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
AUDIO_DIR = os.path.join(STATIC_DIR, "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Environment variables
API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_multilingual_v2")
PUBLIC = os.getenv("PUBLIC_BASE_URL", "http://localhost:8001")

class TtsBody(BaseModel):
    text: str
    voice_id: str | None = None
    model_id: str | None = None
    stability: float | None = 0.7
    similarity_boost: float | None = 0.7
    format: str | None = "mp3"  # mp3|wav|ogg

@app.post("/tts")
def tts(body: TtsBody):
    """
    Convert text to speech using ElevenLabs API
    Returns JSON with text and audio_url
    """
    if not API_KEY:
        raise HTTPException(500, "ELEVENLABS_API_KEY is missing")

    text = (body.text or "").strip()
    if not text:
        raise HTTPException(400, "text is required")

    voice_id = body.voice_id or VOICE_ID
    model_id = body.model_id or MODEL_ID
    fmt = (body.format or "mp3").lower()

    # Cache theo nội dung để tiết kiệm credit
    hash_key = hashlib.sha1(f"{voice_id}|{model_id}|{fmt}|{text}".encode()).hexdigest()
    out_path = os.path.join(AUDIO_DIR, f"{hash_key}.{fmt}")
    
    if os.path.exists(out_path):
        audio_url = f"{PUBLIC}/static/audio/{hash_key}.{fmt}"
        return {"text": text, "audio_url": audio_url, "cached": True}

    # Call ElevenLabs API
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": API_KEY, "Content-Type": "application/json"}
    payload = {
        "text": text,
        "model_id": model_id,
        "voice_settings": {
            "stability": body.stability or 0.7,
            "similarity_boost": body.similarity_boost or 0.7
        }
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code >= 400:
            raise HTTPException(r.status_code, f"ElevenLabs API error: {r.text}")
        
        # Save audio file
        with open(out_path, "wb") as f:
            f.write(r.content)
            
    except requests.exceptions.RequestException as e:
        raise HTTPException(502, f"ElevenLabs TTS error: {e}")

    audio_url = f"{PUBLIC}/static/audio/{hash_key}.{fmt}"
    return {"text": text, "audio_url": audio_url, "cached": False}

@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "ok": True, 
        "service": "voice",
        "api_key_configured": bool(API_KEY),
        "voice_id": VOICE_ID,
        "model_id": MODEL_ID
    }

@app.get("/")
def root():
    """Root endpoint with service info"""
    return {
        "service": "Campus Voice Service",
        "endpoints": {
            "tts": "POST /tts - Convert text to speech",
            "health": "GET /health - Health check",
            "static": "GET /static/audio/{filename} - Audio files"
        }
    }
