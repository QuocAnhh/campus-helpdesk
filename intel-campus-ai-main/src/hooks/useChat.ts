import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message, ChatRequest } from '@/types/chat';
import { chatAPI } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import { tts, AudioPlayer } from '@/services/voice';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  const [autoSpeakEnabled, setAutoSpeakEnabled] = useState(() => {
    const saved = localStorage.getItem('autoSpeakEnabled');
    return saved ? JSON.parse(saved) : true;
  });
  const { toast } = useToast();

  const toggleAutoSpeak = useCallback((enabled: boolean) => {
    setAutoSpeakEnabled(enabled);
    localStorage.setItem('autoSpeakEnabled', JSON.stringify(enabled));
  }, []);

  const playBotResponse = useCallback(async (text: string) => {
    if (!autoSpeakEnabled) return;
    
    try {
      const { audio_url } = await tts(text);
      await AudioPlayer.playAudio(audio_url);
    } catch (error) {
      console.warn('Failed to play TTS audio:', error);
      // Don't show error toast for TTS failures - it's a nice-to-have feature
    }
  }, [autoSpeakEnabled]);

  const sendMessage = useCallback(async (text: string) => {
    const userMessage: Message = {
      id: uuidv4(),
      text,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const request: ChatRequest = {
        channel: 'web',
        text,
        student_id: '12345',
        session_id: sessionId,
      };

      const response = await chatAPI.sendMessage(request);
      
      const botMessage: Message = {
        id: uuidv4(),
        text: response.answer.reply,
        sender: 'bot',
        timestamp: new Date(),
        agentInfo: response.agent_info,
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Auto-play TTS if enabled
      playBotResponse(response.answer.reply);
      
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage: Message = {
        id: uuidv4(),
        text: 'Sorry, I encountered an error. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, errorMessage]);
      
      toast({
        title: "Lỗi kết nối",
        description: "Không thể kết nối tới server. Vui lòng thử lại.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, toast, playBotResponse]);

  return {
    messages,
    isLoading,
    sessionId,
    sendMessage,
    autoSpeakEnabled,
    toggleAutoSpeak,
  };
};