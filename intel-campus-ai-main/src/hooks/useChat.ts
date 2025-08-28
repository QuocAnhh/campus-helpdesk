import { useState, useCallback } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Message, ChatRequest } from '@/types/chat';
import { chatAPI } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => uuidv4());
  const { toast } = useToast();

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
  }, [sessionId, toast]);

  return {
    messages,
    isLoading,
    sessionId,
    sendMessage,
  };
};