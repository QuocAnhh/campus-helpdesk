/**
 * Voice service for Text-to-Speech integration with ElevenLabs
 */

export interface TtsRequest {
  text: string;
  voice_id?: string;
  model_id?: string;
  stability?: number;
  similarity_boost?: number;
  format?: string;
}

export interface TtsResponse {
  text: string;
  audio_url: string;
  cached: boolean;
}

const VOICE_BASE_URL = import.meta.env.VITE_VOICE_BASE_URL || 'http://localhost:8000';

export async function tts(text: string, options?: Partial<TtsRequest>): Promise<TtsResponse> {
  if (!text.trim()) {
    throw new Error('Text is required for TTS');
  }

  const requestBody: TtsRequest = {
    text: text.trim(),
    ...options
  };

  try {
    const response = await fetch(`${VOICE_BASE_URL}/tts`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`TTS request failed: ${response.status} - ${errorText}`);
    }

    const result: TtsResponse = await response.json();
    return result;
  } catch (error) {
    console.error('TTS service error:', error);
    throw error;
  }
}

export async function checkVoiceServiceHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${VOICE_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Audio player with error handling for autoplay policies
 */
export class AudioPlayer {
  private static userHasInteracted = false;
  private static pendingAudio: string[] = [];

  static enableAutoPlay() {
    this.userHasInteracted = true;
    // Play any pending audio
    while (this.pendingAudio.length > 0) {
      const audioUrl = this.pendingAudio.shift();
      if (audioUrl) {
        this.playAudio(audioUrl);
      }
    }
  }

  static async playAudio(audioUrl: string): Promise<boolean> {
    try {
      const audio = new Audio(audioUrl);
      
      // Check if user has interacted (for autoplay policy)
      if (!this.userHasInteracted) {
        this.pendingAudio.push(audioUrl);
        console.log('Audio queued - waiting for user interaction');
        return false;
      }

      await audio.play();
      return true;
    } catch (error) {
      console.error('Failed to play audio:', error);
      
      // If autoplay failed, queue for later
      if (!this.userHasInteracted) {
        this.pendingAudio.push(audioUrl);
      }
      return false;
    }
  }
}

// Initialize audio player on any user interaction
if (typeof window !== 'undefined') {
  const enableAutoPlayOnInteraction = () => {
    AudioPlayer.enableAutoPlay();
    document.removeEventListener('click', enableAutoPlayOnInteraction);
    document.removeEventListener('keydown', enableAutoPlayOnInteraction);
  };

  document.addEventListener('click', enableAutoPlayOnInteraction);
  document.addEventListener('keydown', enableAutoPlayOnInteraction);
}
