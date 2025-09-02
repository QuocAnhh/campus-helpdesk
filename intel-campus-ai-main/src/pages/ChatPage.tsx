import { useChat } from '@/hooks/useChat';
import { MessageList } from '@/components/chat/MessageList';
import { ChatInput } from '@/components/chat/ChatInput';
import { GraduationCap, Settings, LogOut, Ticket, User, Volume2, VolumeX, Phone } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Link } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

const ChatPage = () => {
  const { messages, isLoading, sendMessage, autoSpeakEnabled, toggleAutoSpeak } = useChat();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-gradient-chat flex flex-col">
      {/* Header */}
      <header className="bg-card border-b border-border shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-primary rounded-xl flex items-center justify-center">
              <GraduationCap className="h-6 w-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold">Campus Helpdesk</h1>
              <p className="text-sm text-muted-foreground">
                Welcome, {user?.full_name || user?.username}
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button 
              variant={autoSpeakEnabled ? "default" : "outline"} 
              size="sm"
              onClick={() => toggleAutoSpeak(!autoSpeakEnabled)}
              title={autoSpeakEnabled ? "Turn off auto-speak" : "Turn on auto-speak"}
            >
              {autoSpeakEnabled ? (
                <Volume2 className="h-4 w-4 mr-2" />
              ) : (
                <VolumeX className="h-4 w-4 mr-2" />
              )}
              {autoSpeakEnabled ? "Voice On" : "Voice Off"}
            </Button>
            <Link to="/call">
              <Button variant="outline" size="sm">
                <Phone className="h-4 w-4 mr-2" />
                Voice Call
              </Button>
            </Link>
            <Link to="/self-service">
              <Button variant="ghost" size="sm">
                <User className="h-4 w-4 mr-2" />
                Self-Service
              </Button>
            </Link>
            <Link to="/tickets">
              <Button variant="ghost" size="sm">
                <Ticket className="h-4 w-4 mr-2" />
                Support Tickets
              </Button>
            </Link>
            {user?.role === 'admin' && (
              <Link to="/admin">
                <Button variant="ghost" size="sm">
                  <Settings className="h-4 w-4 mr-2" />
                  Admin
                </Button>
              </Link>
            )}
            <Button variant="outline" size="sm" onClick={logout}>
              <LogOut className="h-4 w-4 mr-2" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Chat Area */}
      <div className="flex-1 max-w-4xl mx-auto w-full flex flex-col">
        <div className="flex-1 overflow-hidden">
          <MessageList messages={messages} isLoading={isLoading} />
        </div>
        <div className="p-4">
          <ChatInput onSendMessage={sendMessage} isLoading={isLoading} />
        </div>
      </div>
    </div>
  );
};

export default ChatPage;