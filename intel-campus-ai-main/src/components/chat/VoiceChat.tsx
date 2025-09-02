import React from 'react';
import { Mic, MicOff, Volume2, Loader2, AlertCircle } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useVoiceChat } from '@/hooks/useVoiceChat';

interface VoiceChatProps {
  sessionId?: string;
  onSessionChange?: (sessionId: string) => void;
  className?: string;
  autoPlay?: boolean;
}

export function VoiceChat({ 
  sessionId, 
  onSessionChange, 
  className,
  autoPlay = true 
}: VoiceChatProps) {
  const {
    messages,
    isRecording,
    isProcessing,
    error,
    currentSessionId,
    toggleRecording,
    clearError,
    playAudio
  } = useVoiceChat({
    sessionId,
    onSessionChange,
    autoPlay
  });

  return (
    <div className={cn("flex flex-col h-full bg-white rounded-lg shadow-sm", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900">Chat Giọng Nói</h3>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          {currentSessionId && (
            <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-md">
              Session: {currentSessionId.slice(0, 8)}...
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <Mic className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Nhấn vào micro để bắt đầu trò chuyện bằng giọng nói</p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex",
                message.type === 'user' ? 'justify-end' : 'justify-start'
              )}
            >
              <div
                className={cn(
                  "max-w-xs lg:max-w-md px-4 py-2 rounded-lg",
                  message.type === 'user'
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 text-gray-900'
                )}
              >
                <p className="text-sm">{message.text}</p>
                
                {/* Audio player for bot messages */}
                {message.type === 'bot' && message.audioUrl && (
                  <div className="mt-2 flex items-center space-x-2">
                    <button
                      onClick={() => playAudio(message.audioUrl!)}
                      className="flex items-center space-x-1 text-xs text-gray-600 hover:text-gray-800 transition-colors"
                    >
                      <Volume2 className="w-4 h-4" />
                      <span>Phát audio</span>
                    </button>
                  </div>
                )}
                
                <div className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Error Display */}
      {error && (
        <div className="mx-4 mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2 text-red-700">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 text-sm"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Recording Controls */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex justify-center">
          <button
            onClick={toggleRecording}
            disabled={isProcessing}
            className={cn(
              "relative w-16 h-16 rounded-full flex items-center justify-center transition-all duration-200 focus:outline-none focus:ring-4 focus:ring-opacity-50",
              isRecording
                ? "bg-red-500 hover:bg-red-600 focus:ring-red-500 animate-pulse"
                : "bg-blue-500 hover:bg-blue-600 focus:ring-blue-500",
              isProcessing && "opacity-50 cursor-not-allowed"
            )}
          >
            {isProcessing ? (
              <Loader2 className="w-6 h-6 text-white animate-spin" />
            ) : isRecording ? (
              <MicOff className="w-6 h-6 text-white" />
            ) : (
              <Mic className="w-6 h-6 text-white" />
            )}
          </button>
        </div>
        
        <div className="text-center mt-2">
          <p className="text-sm text-gray-600">
            {isProcessing
              ? "Đang xử lý..."
              : isRecording
              ? "Nhấn để dừng ghi âm"
              : "Nhấn để bắt đầu ghi âm"
            }
          </p>
        </div>
      </div>
    </div>
  );
}
