"""
Voice services for Whisper (STT) and ElevenLabs (TTS) integration
"""

import os
import httpx
import logging
from typing import Optional, BinaryIO
from pathlib import Path

logger = logging.getLogger(__name__)

class WhisperService:
    """OpenAI Whisper Speech-to-Text service"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }
    
    async def transcribe_audio(self, audio_file: BinaryIO, filename: str = "audio.webm") -> Optional[str]:
        """
        Transcribe audio file using Whisper API
        
        Args:
            audio_file: Binary audio file
            filename: Original filename for content type detection
            
        Returns:
            Transcribed text or None if error
        """
        try:
            files = {
                "file": (filename, audio_file, "audio/webm"),
                "model": (None, "whisper-1"),
                "language": (None, "vi"),  # Vietnamese
                "response_format": (None, "text")
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers=self.headers,
                    files=files
                )
                
                if response.status_code == 200:
                    transcript = response.text.strip()
                    logger.info(f"Whisper transcription successful: {transcript}")
                    return transcript
                else:
                    logger.error(f"Whisper API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.exception(f"Error transcribing audio: {e}")
            return None


class ElevenLabsService:
    """ElevenLabs Text-to-Speech service"""
    
    def __init__(self, api_key: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        self.api_key = api_key
        self.voice_id = voice_id  # Default voice ID (Rachel)
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
    
    async def text_to_speech(self, text: str, output_path: str) -> bool:
        """
        Convert text to speech using ElevenLabs API
        
        Args:
            text: Text to convert
            output_path: Path to save the generated audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{self.voice_id}",
                    headers=self.headers,
                    json=data
                )
                
                if response.status_code == 200:
                    # Ensure output directory exists
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    
                    # Save audio file
                    with open(output_path, "wb") as f:
                        f.write(response.content)
                    
                    logger.info(f"TTS audio saved to: {output_path}")
                    return True
                else:
                    logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.exception(f"Error generating speech: {e}")
            return False


class VoiceManager:
    """Manager class for voice operations"""
    
    def __init__(self, openai_api_key: str, elevenlabs_api_key: str, 
                 static_audio_dir: str = "/tmp/static/audio"):
        self.whisper = WhisperService(openai_api_key)
        self.elevenlabs = ElevenLabsService(elevenlabs_api_key)
        self.static_audio_dir = Path(static_audio_dir)
        self.static_audio_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_voice_chat(self, audio_file: BinaryIO, filename: str,
                               ask_agent_func) -> dict:
        """
        Complete voice chat processing pipeline
        
        Args:
            audio_file: Input audio file
            filename: Original filename
            ask_agent_func: Async function to call for generating response
            
        Returns:
            Dict with transcript, response text, and audio URL
        """
        try:
            # Step 1: Speech to Text
            transcript = await self.whisper.transcribe_audio(audio_file, filename)
            if not transcript:
                return {
                    "error": "Failed to transcribe audio",
                    "transcript": None,
                    "text": None,
                    "audio_url": None
                }
            
            # Step 2: Get bot response
            try:
                # Call the async agent function
                bot_response = await ask_agent_func(transcript)
                if isinstance(bot_response, dict):
                    response_text = bot_response.get('reply', str(bot_response))
                else:
                    response_text = str(bot_response)
            except Exception as e:
                logger.exception(f"Error calling ask_agent: {e}")
                response_text = "Xin lỗi, tôi không thể xử lý yêu cầu này."
            
            # Step 3: Text to Speech
            import uuid
            audio_filename = f"tts_{uuid.uuid4().hex}.mp3"
            audio_path = self.static_audio_dir / audio_filename
            
            tts_success = await self.elevenlabs.text_to_speech(response_text, str(audio_path))
            
            audio_url = None
            if tts_success:
                # Generate public URL (adjust based on your static file serving setup)
                audio_url = f"/static/audio/{audio_filename}"
            
            return {
                "transcript": transcript,
                "text": response_text,
                "audio_url": audio_url,
                "error": None if tts_success else "Failed to generate audio"
            }
            
        except Exception as e:
            logger.exception(f"Error in voice chat processing: {e}")
            return {
                "error": str(e),
                "transcript": None,
                "text": None,
                "audio_url": None
            }
