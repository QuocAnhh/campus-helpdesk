import { useState, useCallback, useRef, useEffect } from 'react';

export type CallState = 'idle' | 'connecting' | 'live' | 'ending' | 'ended';

export interface Caption {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  isPartial?: boolean;
}

export interface HistoryItem {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useVoiceCall = () => {
  const [callState, setCallState] = useState<CallState>('idle');
  const [isMuted, setIsMuted] = useState(false);
  const [isPTTActive, setIsPTTActive] = useState(false);
  const [captionsEnabled, setCaptionsEnabled] = useState(true);
  const [autoTTSEnabled, setAutoTTSEnabled] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [captions, setCaptions] = useState<Caption[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [callDuration, setCallDuration] = useState(0);
  const [latency, setLatency] = useState<number | null>(null);
  const [volume, setVolume] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioQueueRef = useRef<HTMLAudioElement[]>([]);
  const callStartTimeRef = useRef<number | null>(null);
  const sessionIdRef = useRef<string>(`call-${Date.now()}`);
  const audioChunksRef = useRef<Blob[]>([]);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  // Timer for call duration
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (callState === 'live' && callStartTimeRef.current) {
      interval = setInterval(() => {
        setCallDuration(Date.now() - callStartTimeRef.current!);
      }, 1000);
    }

    return () => clearInterval(interval);
  }, [callState]);

  // Health check for latency
  useEffect(() => {
    const checkLatency = async () => {
      const start = Date.now();
      try {
        await fetch(`${API_BASE}/health`);
        setLatency(Date.now() - start);
      } catch {
        setLatency(null);
      }
    };

    let interval: NodeJS.Timeout;
    if (callState === 'live') {
      checkLatency(); // Initial check
      interval = setInterval(checkLatency, 5000);
    }

    return () => clearInterval(interval);
  }, [callState]);

  // Audio volume monitoring
  useEffect(() => {
    if (!analyserRef.current || !streamRef.current) return;

    const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
    let animationId: number;

    const updateVolume = () => {
      if (analyserRef.current) {
        analyserRef.current.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        setVolume(average / 255);
      }
      animationId = requestAnimationFrame(updateVolume);
    };

    if (isRecording && !isMuted) {
      updateVolume();
    }

    return () => cancelAnimationFrame(animationId);
  }, [isRecording, isMuted]);

  const startCall = useCallback(async () => {
    try {
      setCallState('connecting');
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 48000,
        }
      });

      streamRef.current = stream;
      
      // Setup audio context for volume monitoring
      audioContextRef.current = new AudioContext();
      const source = audioContextRef.current.createMediaStreamSource(stream);
      analyserRef.current = audioContextRef.current.createAnalyser();
      analyserRef.current.fftSize = 256;
      source.connect(analyserRef.current);

      // Setup MediaRecorder
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];
        
        if (audioBlob.size > 0) {
          await processAudioBlob(audioBlob);
        }
      };

      // Simulate connection delay
      setTimeout(() => {
        setCallState('live');
        callStartTimeRef.current = Date.now();
      }, Math.random() * 500 + 300); // 300-800ms delay

    } catch (error) {
      console.error('Failed to start call:', error);
      setCallState('ended');
    }
  }, []);

  const endCall = useCallback(() => {
    setCallState('ending');
    
    // Stop recording
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }

    // Stop stream
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Stop all queued audio
    audioQueueRef.current.forEach(audio => {
      audio.pause();
      audio.src = '';
    });
    audioQueueRef.current = [];

    setTimeout(() => {
      setCallState('ended');
      callStartTimeRef.current = null;
      setCallDuration(0);
    }, 1000);
  }, [isRecording]);

  const toggleMute = useCallback(() => {
    if (streamRef.current) {
      const audioTrack = streamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = isMuted;
        setIsMuted(!isMuted);
      }
    }
  }, [isMuted]);

  const startPTT = useCallback(() => {
    if (callState !== 'live' || isRecording) return;
    
    setIsPTTActive(true);
    setIsRecording(true);
    
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.start();
    }
  }, [callState, isRecording]);

  const stopPTT = useCallback(() => {
    if (!isPTTActive || !isRecording) return;
    
    setIsPTTActive(false);
    setIsRecording(false);
    
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, [isPTTActive, isRecording]);

  const processAudioBlob = useCallback(async (audioBlob: Blob) => {
    try {
      // Add user caption placeholder
      const userCaptionId = `user-${Date.now()}`;
      setCaptions(prev => [...prev, {
        id: userCaptionId,
        text: 'Processing...',
        sender: 'user',
        timestamp: new Date(),
        isPartial: true
      }]);

      // Send to voice chat endpoint
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      formData.append('session_id', sessionIdRef.current);

      const response = await fetch(`${API_BASE}/voice-chat`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error(`Voice chat failed: ${response.status}`);
      }

      const result = await response.json();
      
      // Update user caption with transcript
      setCaptions(prev => prev.map(cap => 
        cap.id === userCaptionId 
          ? { ...cap, text: result.transcript || 'Unable to transcribe', isPartial: false }
          : cap
      ));

      // Add to history
      const historyItem: HistoryItem = {
        id: `history-user-${Date.now()}`,
        text: result.transcript || 'Unable to transcribe',
        sender: 'user',
        timestamp: new Date()
      };
      
      setHistory(prev => [...prev.slice(-4), historyItem]);

      // Add bot response
      if (result.text) {
        const botCaption: Caption = {
          id: `bot-${Date.now()}`,
          text: result.text,
          sender: 'bot',
          timestamp: new Date()
        };
        
        setCaptions(prev => [...prev, botCaption]);
        
        const botHistory: HistoryItem = {
          id: `history-bot-${Date.now()}`,
          text: result.text,
          sender: 'bot',
          timestamp: new Date()
        };
        
        setHistory(prev => [...prev.slice(-4), botHistory]);

        // Play audio if available and auto-TTS enabled
        if (result.audio_url && autoTTSEnabled) {
          playAudio(result.audio_url);
        }
      }

    } catch (error) {
      console.error('Failed to process audio:', error);
      
      // Update user caption with error
      setCaptions(prev => prev.map(cap => 
        cap.id.startsWith('user-') && cap.isPartial
          ? { ...cap, text: 'Failed to process audio', isPartial: false }
          : cap
      ));
    }
  }, [autoTTSEnabled]);

  const playAudio = useCallback((audioUrl: string) => {
    const audio = new Audio(audioUrl);
    
    audio.onloadeddata = () => {
      audio.play().catch(console.error);
    };
    
    audio.onended = () => {
      audioQueueRef.current = audioQueueRef.current.filter(a => a !== audio);
    };
    
    audioQueueRef.current.push(audio);
  }, []);

  const formatDuration = useCallback((ms: number) => {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (callState !== 'live') return;

      switch (event.code) {
        case 'KeyM':
          if (!event.ctrlKey && !event.metaKey) {
            event.preventDefault();
            toggleMute();
          }
          break;
        case 'Space':
          if (!isPTTActive) {
            event.preventDefault();
            startPTT();
          }
          break;
        case 'Escape':
          event.preventDefault();
          endCall();
          break;
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (event.code === 'Space' && isPTTActive) {
        event.preventDefault();
        stopPTT();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [callState, isPTTActive, toggleMute, startPTT, stopPTT, endCall]);

  return {
    // State
    callState,
    isMuted,
    isPTTActive,
    captionsEnabled,
    autoTTSEnabled,
    isRecording,
    captions,
    history: history.slice(-5), // Only last 5 items
    callDuration: formatDuration(callDuration),
    latency,
    volume,
    sessionId: sessionIdRef.current,

    // Actions
    startCall,
    endCall,
    toggleMute,
    startPTT,
    stopPTT,
    setCaptionsEnabled,
    setAutoTTSEnabled,

    // Utils
    formatDuration,
  };
};
