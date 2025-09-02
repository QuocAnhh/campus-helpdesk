import { useState, useRef, useCallback, useEffect } from 'react';

interface VoiceChatMessage {
  id: string;
  type: 'user' | 'bot';
  text: string;
  audioUrl?: string;
  timestamp: Date;
}

interface VoiceChatResponse {
  session_id: string;
  transcript: string;
  text: string;
  audio_url?: string;
}

interface UseVoiceChatOptions {
  sessionId?: string;
  onSessionChange?: (sessionId: string) => void;
  autoPlay?: boolean;
}

interface UseVoiceChatReturn {
  messages: VoiceChatMessage[];
  isRecording: boolean;
  isProcessing: boolean;
  error: string | null;
  currentSessionId: string | undefined;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  toggleRecording: () => void;
  clearMessages: () => void;
  clearError: () => void;
  playAudio: (audioUrl: string) => void;
}

export function useVoiceChat({
  sessionId,
  onSessionChange,
  autoPlay = true
}: UseVoiceChatOptions = {}): UseVoiceChatReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<VoiceChatMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentSessionId, setCurrentSessionId] = useState(sessionId);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  // Initialize audio context for better browser compatibility
  const initializeAudio = useCallback(async (): Promise<boolean> => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      });
      
      streamRef.current = stream;
      
      // Check MediaRecorder support and choose best format
      const options: MediaRecorderOptions = {};
      if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
        options.mimeType = 'audio/webm;codecs=opus';
      } else if (MediaRecorder.isTypeSupported('audio/webm')) {
        options.mimeType = 'audio/webm';
      } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
        options.mimeType = 'audio/mp4';
      } else {
        console.warn('No supported audio format found, using default');
      }

      const mediaRecorder = new MediaRecorder(stream, options);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        await handleRecordingStop();
      };

      return true;
    } catch (err) {
      console.error('Error initializing audio:', err);
      setError('Không thể truy cập microphone. Vui lòng cho phép truy cập và thử lại.');
      return false;
    }
  }, []);

  const handleRecordingStop = useCallback(async () => {
    if (audioChunksRef.current.length === 0) {
      setError('Không có dữ liệu audio. Vui lòng thử lại.');
      return;
    }

    setIsProcessing(true);
    
    try {
      // Create audio blob
      const audioBlob = new Blob(audioChunksRef.current, { 
        type: mediaRecorderRef.current?.mimeType || 'audio/webm' 
      });
      
      // Prepare form data
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');
      if (currentSessionId) {
        formData.append('session_id', currentSessionId);
      }

      // Send to backend
      const response = await fetch('/api/voice-chat', {
        method: 'POST',
        body: formData,
        headers: {
          // Don't set Content-Type, let browser set it with boundary
          ...(localStorage.getItem('token') && {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          })
        }
      });

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`Server error: ${response.status} - ${errorData}`);
      }

      const result: VoiceChatResponse = await response.json();
      
      // Update session ID if changed
      if (result.session_id && result.session_id !== currentSessionId) {
        setCurrentSessionId(result.session_id);
        onSessionChange?.(result.session_id);
      }

      // Add messages to chat
      const userMessage: VoiceChatMessage = {
        id: `user-${Date.now()}`,
        type: 'user',
        text: result.transcript,
        timestamp: new Date()
      };

      const botMessage: VoiceChatMessage = {
        id: `bot-${Date.now()}`,
        type: 'bot',
        text: result.text,
        audioUrl: result.audio_url,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, userMessage, botMessage]);

      // Auto-play bot response audio
      if (autoPlay && result.audio_url) {
        setTimeout(() => {
          playAudio(result.audio_url);
        }, 500);
      }

    } catch (err) {
      console.error('Error processing voice chat:', err);
      setError(err instanceof Error ? err.message : 'Có lỗi xảy ra khi xử lý giọng nói');
    } finally {
      setIsProcessing(false);
      audioChunksRef.current = [];
    }
  }, [currentSessionId, onSessionChange, autoPlay]);

  const startRecording = useCallback(async () => {
    setError(null);
    
    if (!mediaRecorderRef.current) {
      const initialized = await initializeAudio();
      if (!initialized) return;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
      audioChunksRef.current = [];
      mediaRecorderRef.current.start(250); // Collect data every 250ms
      setIsRecording(true);
    }
  }, [initializeAudio]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording]);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const playAudio = useCallback((audioUrl: string) => {
    const audio = new Audio(audioUrl);
    audio.play().catch(console.error);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  return {
    messages,
    isRecording,
    isProcessing,
    error,
    currentSessionId,
    startRecording,
    stopRecording,
    toggleRecording,
    clearMessages,
    clearError,
    playAudio
  };
}
