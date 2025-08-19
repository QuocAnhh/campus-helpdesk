export const TypingIndicator = () => {
  return (
    <div className="flex justify-start mb-4">
      <div className="message-bubble-bot typing-indicator">
        <div className="flex items-center space-x-1">
          <span className="text-sm">Đang trả lời</span>
          <div className="flex space-x-1">
            <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce"></div>
            <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-1.5 h-1.5 bg-current rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};