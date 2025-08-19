import { Message } from '@/types/chat';
import { formatDistanceToNow } from 'date-fns';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble = ({ message }: MessageBubbleProps) => {
  const isUser = message.sender === 'user';
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] ${isUser ? 'order-2' : 'order-1'}`}>
        <div className={isUser ? 'message-bubble-user' : 'message-bubble-bot'}>
          <p className="text-sm leading-relaxed">{message.text}</p>
        </div>
        <div className={`flex items-center gap-2 mt-1 px-2 ${isUser ? 'justify-end' : 'justify-start'}`}>
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(message.timestamp, { addSuffix: true })}
          </span>
          {message.agentInfo && !isUser && (
            <span className="text-xs text-muted-foreground">
              • {message.agentInfo.name}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};