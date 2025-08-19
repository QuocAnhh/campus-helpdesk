import { useEffect, useRef } from 'react';
import { Message } from '@/types/chat';
import { MessageBubble } from './MessageBubble';
import { TypingIndicator } from './TypingIndicator';

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
}

export const MessageList = ({ messages, isLoading }: MessageListProps) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
      <div className="space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <div className="bg-gradient-primary bg-clip-text text-transparent text-lg font-semibold mb-2">
              Chào mừng đến với Campus Helpdesk! 👋
            </div>
            <p className="text-muted-foreground">
              Tôi là trợ lý AI của trường. Hãy đặt câu hỏi và tôi sẽ giúp bạn!
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))
        )}
        
        {isLoading && <TypingIndicator />}
        
        <div ref={messagesEndRef} />
      </div>
    </div>
  );
};