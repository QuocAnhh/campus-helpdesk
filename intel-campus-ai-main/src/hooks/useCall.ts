import { useState, useCallback, useRef, useEffect } from 'react';
import { useDevices } from './useDevices';

export type CallState = 'idle' | 'connecting' | 'live' | 'ending' | 'ended';

export interface Caption {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export interface CallHistory {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useCall = () => {
  const [callState, setCallState] = useState<CallState>('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [isPTTActive, setIsPTTActive] = useState(false);
  const [captionsEnabled, setCaptionsEnabled] = useState(true);
  const [autoTTSEnabled, setAutoTTSEnabled] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [history, setHistory] = useState<CallHistory[]>([]);
  const [callDuration, setCallDuration] = useState(0);
  const [latency, setLatency] = useState<number | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioQueueRef = useRef<HTMLAudioElement[]>([]);
  const callStartTimeRef = useRef<number | null>(null);
  const sessionIdRef = useRef<string>(`call-${Date.now()}`);

  const { selectedInput, permissionGranted, requestPermissions } = useDevices();

  // Timer for call duration
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (callState === 'live' && callStartTimeRef.current) {
      interval = setInterval(() => {
        setCallDuration(Date.now() - callStartTimeRef.current!);
      }, 1000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [callState]);

  // Health check and latency monitoring
  useEffect(() => {
    let interval: NodeJS.Timeout;

    const checkHealth = async () => {
      const start = Date.now();
      try {
        const response = await fetch(`${API_BASE}/health`);
        if (response.ok) {
          setLatency(Date.now() - start);
        }
      } catch (error) {
        console.error('Health check failed:', error);
        setLatency(null);
      }
    };

    if (callState === 'live') {
      checkHealth(); // Initial check
      interval = setInterval(checkHealth, 5000); // Every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [callState]);

  const addCaption = useCallback((text: string, sender: 'user' | 'bot') => {
    const caption: Caption = {
      id: `caption-${Date.now()}-${Math.random()}`,
      text,
      sender,
      timestamp: new Date()
    };
    
    setCaptions(prev => [...prev.slice(-19), caption]); // Keep last 20 captions
    
    // Add to history
    const historyItem: CallHistory = {
      id: caption.id,
      text,
      sender,
      timestamp: new Date()
    };
    setHistory(prev => [...prev.slice(-4), historyItem]); // Keep last 5 items
  }, []);

  const playAudioQueue = useCallback(async (audioUrl: string) => {
    if (!autoTTSEnabled) return;

    try {
      const audio = new Audio(audioUrl);
      
      // Set audio output device if supported
      if ('setSinkId' in audio && selectedInput) {
        try {
          await (audio as any).setSinkId(selectedInput);
        } catch (error) {
          console.warn('Failed to set audio output device:', error);
        }
      }

      audioQueueRef.current.push(audio);
      
      audio.onended = () => {
        audioQueueRef.current = audioQueueRef.current.filter(a => a !== audio);
      };

      audio.onerror = () => {
        audioQueueRef.current = audioQueueRef.current.filter(a => a !== audio);
      };

      await audio.play();
    } catch (error) {
      console.error('Failed to play audio:', error);
    }
  }, [autoTTSEnabled, selectedInput]);

  const sendAudioChunk = useCallback(async (audioBlob: Blob, isLast = false) => {
    try {
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'audio.webm');
      formData.append('session_id', sessionIdRef.current);
      
      const response = await fetch(`${API_BASE}/voice-chat`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        
        if (result.transcript && captionsEnabled) {
          addCaption(result.transcript, 'user');
        }
        
        if (result.text) {
          if (captionsEnabled) {
            addCaption(result.text, 'bot');
          }
          
          if (result.audio_url) {
            await playAudioQueue(result.audio_url);
          }
        }
      }
    } catch (error) {
      console.error('Failed to send audio chunk:', error);
    }
  }, [addCaption, captionsEnabled, playAudioQueue]);

  const startRecording = useCallback(async () => {
    if (!permissionGranted) {
      const granted = await requestPermissions();
      if (!granted) return false;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          deviceId: selectedInput ? { exact: selectedInput } : undefined,
          sampleRate: 48000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        }
      });

      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorderRef.current = mediaRecorder;
      
      const audioChunks: Blob[] = [];
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        if (audioChunks.length > 0) {
          const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
          sendAudioChunk(audioBlob, true);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      return true;
    } catch (error) {
      console.error('Failed to start recording:', error);
      return false;
    }
  }, [permissionGranted, requestPermissions, selectedInput, sendAudioChunk]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
  }, [isRecording]);

  const startCall = useCallback(async () => {
    setCallState('connecting');
    
    // Simulate connection delay
    setTimeout(() => {
      setCallState('live');
      callStartTimeRef.current = Date.now();
      addCaption('Call started - speak naturally or use push-to-talk', 'bot');
    }, 800);
  }, [addCaption]);

  const endCall = useCallback(() => {
    setCallState('ending');
    
    // Stop recording
    stopRecording();
    
    // Stop all playing audio
    audioQueueRef.current.forEach(audio => {
      audio.pause();
      audio.currentTime = 0;
    });
    audioQueueRef.current = [];

    // End call after brief delay
    setTimeout(() => {
      setCallState('ended');
      callStartTimeRef.current = null;
      setCallDuration(0);
    }, 1000);
  }, [stopRecording]);

  const toggleMute = useCallback(() => {
    setIsMuted(prev => !prev);
    
    if (streamRef.current) {
      streamRef.current.getAudioTracks().forEach(track => {
        track.enabled = isMuted;
      });
    }
  }, [isMuted]);

  const togglePTT = useCallback((active: boolean) => {
    setIsPTTActive(active);
    
    if (active && !isRecording) {
      startRecording();
    } else if (!active && isRecording) {
      stopRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const toggleCaptions = useCallback(() => {
    setCaptionsEnabled(prev => !prev);
  }, []);

  const toggleAutoTTS = useCallback(() => {
    setAutoTTSEnabled(prev => !prev);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current) {
        mediaRecorderRef.current.stop();
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      audioQueueRef.current.forEach(audio => {
        audio.pause();
      });
    };
  }, []);

  return {
    callState,
    isMuted,
    isPTTActive,
    captionsEnabled,
    autoTTSEnabled,
    isRecording,
    captions,
    history,
    callDuration,
    latency,
    startCall,
    endCall,
    toggleMute,
    togglePTT,
    toggleCaptions,
    toggleAutoTTS,
    startRecording,
    stopRecording,
  };
};
