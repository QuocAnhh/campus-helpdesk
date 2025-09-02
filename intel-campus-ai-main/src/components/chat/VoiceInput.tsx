import React, { useState } from 'react';
import { Mic, MicOff, Volume2, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useVoiceChat } from '@/hooks/useVoiceChat';

interface VoiceInputProps {
  onTranscript?: (text: string) => void;
  onResponse?: (text: string, audioUrl?: string) => void;
  sessionId?: string;
  disabled?: boolean;
  className?: string;
}

export function VoiceInput({
  onTranscript,
  onResponse,
  sessionId,
  disabled = false,
  className
}: VoiceInputProps) {
  const [showFullChat, setShowFullChat] = useState(false);
  
  const {
    messages,
    isRecording,
    isProcessing,
    error,
    toggleRecording,
    clearError,
    playAudio
  } = useVoiceChat({
    sessionId,
    autoPlay: false, // Don't auto-play in compact mode
    onSessionChange: () => {}
  });

  // Handle new voice responses
  React.useEffect(() => {
    if (messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      if (lastMessage.type === 'bot') {
        onResponse?.(lastMessage.text, lastMessage.audioUrl);
      } else if (lastMessage.type === 'user') {
        onTranscript?.(lastMessage.text);
      }
    }
  }, [messages, onTranscript, onResponse]);

  if (showFullChat) {
    return (
      <div className={cn("w-full bg-white rounded-lg border shadow-sm", className)}>
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b">
          <h4 className="text-sm font-medium">Voice Chat</h4>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowFullChat(false)}
          >
            ✕
          </Button>
        </div>

        {/* Messages */}
        <div className="max-h-48 overflow-y-auto p-3 space-y-2">
          {messages.length === 0 ? (
            <p className="text-xs text-gray-500 text-center">No voice messages yet</p>
          ) : (
            messages.slice(-5).map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex",
                  message.type === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={cn(
                    "max-w-[80%] px-2 py-1 rounded text-xs",
                    message.type === 'user'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-900'
                  )}
                >
                  <p>{message.text}</p>
                  {message.type === 'bot' && message.audioUrl && (
                    <button
                      onClick={() => playAudio(message.audioUrl!)}
                      className="flex items-center space-x-1 text-xs text-gray-600 hover:text-gray-800 mt-1"
                    >
                      <Volume2 className="w-3 h-3" />
                      <span>Play</span>
                    </button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mx-3 mb-2 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
            {error}
            <button onClick={clearError} className="ml-2 text-red-500">✕</button>
          </div>
        )}

        {/* Controls */}
        <div className="p-3 border-t flex justify-center">
          <Button
            onClick={toggleRecording}
            disabled={disabled || isProcessing}
            size="sm"
            className={cn(
              "w-10 h-10 rounded-full p-0",
              isRecording
                ? "bg-red-500 hover:bg-red-600 animate-pulse"
                : "bg-blue-500 hover:bg-blue-600"
            )}
          >
            {isProcessing ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : isRecording ? (
              <MicOff className="w-4 h-4" />
            ) : (
              <Mic className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      {/* Compact voice button */}
      <Button
        onClick={toggleRecording}
        disabled={disabled || isProcessing}
        size="sm"
        variant={isRecording ? "destructive" : "outline"}
        className={cn(
          "w-9 h-9 p-0",
          isRecording && "animate-pulse"
        )}
      >
        {isProcessing ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : isRecording ? (
          <MicOff className="w-4 h-4" />
        ) : (
          <Mic className="w-4 h-4" />
        )}
      </Button>

      {/* Expand button */}
      <Button
        onClick={() => setShowFullChat(true)}
        size="sm"
        variant="ghost"
        className="text-xs"
      >
        Voice History
      </Button>

      {/* Error indicator */}
      {error && (
        <div className="text-xs text-red-600 max-w-32 truncate" title={error}>
          Error: {error}
        </div>
      )}
    </div>
  );
}
