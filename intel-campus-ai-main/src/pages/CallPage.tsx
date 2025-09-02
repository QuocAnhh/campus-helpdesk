import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, PhoneCall, Timer, Wifi, WifiOff, Bot, User, ArrowLeft, Sparkles, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { CallControls } from '@/components/CallControls';
import { VoiceVisualizer } from '@/components/VoiceVisualizer';
import { useCall, type CallState, type Caption, type CallHistory } from '@/hooks/useCall';
import { useAuth } from '@/context/AuthContext';
import { Link } from 'react-router-dom';

const formatDuration = (ms: number): string => {
  const seconds = Math.floor(ms / 1000);
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
};

const getCallStateText = (state: CallState): string => {
  switch (state) {
    case 'idle': return 'Ready to Call';
    case 'connecting': return 'Connecting...';
    case 'live': return 'Live';
    case 'ending': return 'Ending...';
    case 'ended': return 'Call Ended';
    default: return 'Unknown';
  }
};

const getCallStateColor = (state: CallState): string => {
  switch (state) {
    case 'idle': return 'bg-slate-500';
    case 'connecting': return 'bg-amber-500 animate-pulse';
    case 'live': return 'bg-emerald-500 shadow-emerald-500/50';
    case 'ending': return 'bg-orange-500';
    case 'ended': return 'bg-red-500';
    default: return 'bg-slate-500';
  }
};

const CaptionItem: React.FC<{ caption: Caption }> = ({ caption }) => (
  <motion.div
    initial={{ opacity: 0, y: 20, scale: 0.95 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    exit={{ opacity: 0, y: -20, scale: 0.95 }}
    transition={{ type: "spring", damping: 25, stiffness: 300 }}
    className={`flex gap-3 p-4 rounded-xl backdrop-blur-md border border-white/10 ${
      caption.sender === 'user' 
        ? 'bg-gradient-to-r from-blue-500/20 to-cyan-500/20 ml-8 shadow-blue-500/20' 
        : 'bg-gradient-to-r from-emerald-500/20 to-teal-500/20 mr-8 shadow-emerald-500/20'
    } shadow-lg`}
  >
    <motion.div 
      className="flex-shrink-0"
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ delay: 0.1 }}
    >
      {caption.sender === 'user' ? (
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-cyan-500 flex items-center justify-center">
          <User className="w-4 h-4 text-white" />
        </div>
      ) : (
        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-emerald-500 to-teal-500 flex items-center justify-center animate-pulse">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}
    </motion.div>
    <div className="flex-1 min-w-0">
      <motion.p 
        className="text-sm text-white break-words leading-relaxed font-medium"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        style={{ fontFamily: 'Inter, sans-serif' }}
      >
        {caption.text}
      </motion.p>
      <motion.p 
        className="text-xs text-slate-400 mt-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        style={{ fontFamily: 'JetBrains Mono, monospace' }}
      >
        {caption.timestamp.toLocaleTimeString()}
      </motion.p>
    </div>
  </motion.div>
);

const HistoryItem: React.FC<{ item: CallHistory }> = ({ item }) => (
  <div className={`text-sm p-2 rounded ${
    item.sender === 'user' ? 'bg-blue-500/10 text-blue-200' : 'bg-gray-500/10 text-gray-200'
  }`}>
    <div className="flex items-center gap-2 mb-1">
      {item.sender === 'user' ? (
        <User className="w-3 h-3" />
      ) : (
        <Bot className="w-3 h-3" />
      )}
      <span className="text-xs opacity-70">
        {item.timestamp.toLocaleTimeString()}
      </span>
    </div>
    <p className="line-clamp-2">{item.text}</p>
  </div>
);

const CallPage: React.FC = () => {
  const { user } = useAuth();
  const {
    callState,
    isMuted,
    isPTTActive,
    captionsEnabled,
    autoTTSEnabled,
    isRecording,
    captions,
    history,
    callDuration,
    latency,
    startCall,
    endCall,
    toggleMute,
    togglePTT,
    toggleCaptions,
    toggleAutoTTS,
  } = useCall();

  const [stream, setStream] = useState<MediaStream | null>(null);

  // Get user media when call is live
  useEffect(() => {
    let currentStream: MediaStream | null = null;

    if (callState === 'live') {
      navigator.mediaDevices.getUserMedia({ audio: true })
        .then((mediaStream) => {
          currentStream = mediaStream;
          setStream(mediaStream);
        })
        .catch(console.error);
    }

    return () => {
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
        setStream(null);
      }
    };
  }, [callState]);

  const renderIdleState = () => (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="flex flex-col items-center justify-center h-full px-8"
    >
      <div className="text-center mb-12">
        <motion.div
          initial={{ y: -30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="mb-6"
        >
          <Sparkles className="w-16 h-16 text-purple-400 mx-auto mb-4" />
        </motion.div>
        
        <motion.h1 
          className="text-6xl font-black bg-gradient-to-r from-white via-purple-200 to-cyan-300 bg-clip-text text-transparent mb-6 tracking-tight leading-tight"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Campus Helpdesk
        </motion.h1>
        
        <motion.h2
          className="text-3xl font-bold text-white mb-4 tracking-wide"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.4 }}
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Voice Assistant
        </motion.h2>
        
        <motion.p 
          className="text-xl text-slate-300 mb-12 max-w-2xl leading-relaxed font-medium"
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.5 }}
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          Start a voice conversation with our AI assistant. Get instant help with your campus questions.
        </motion.p>
        
        {/* Call Button */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.6, type: "spring", damping: 15 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="relative"
        >
          {/* Pulsing ring */}
          <motion.div
            className="absolute inset-0 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 opacity-30"
            animate={{ 
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.1, 0.3]
            }}
            transition={{ 
              duration: 2, 
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          
          {/* Main button */}
          <Button
            size="lg"
            onClick={startCall}
            className="relative w-40 h-40 rounded-full bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-600 hover:to-cyan-600 text-white shadow-2xl shadow-emerald-500/25 border-4 border-white/20 backdrop-blur-md transition-all duration-300"
          >
            <div className="flex flex-col items-center gap-3">
              <motion.div
                animate={{ rotate: [0, 5, -5, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Phone className="w-16 h-16" />
              </motion.div>
              <span className="text-xl font-black tracking-wider uppercase" style={{ fontFamily: 'Inter, sans-serif' }}>
                Start Call
              </span>
            </div>
          </Button>
        </motion.div>
      </div>

      {/* User welcome and navigation */}
      <motion.div 
        className="text-center"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.7 }}
      >
        <p className="text-slate-400 mb-6 text-lg font-medium" style={{ fontFamily: 'Inter, sans-serif' }}>
          Welcome, <span className="font-bold text-transparent bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text">{user?.full_name || user?.username}</span>
        </p>
        
        <Link 
          to="/chat" 
          className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors duration-200 text-lg font-semibold backdrop-blur-md bg-white/5 px-6 py-3 rounded-full border border-white/10 hover:border-blue-400/50"
          style={{ fontFamily: 'Inter, sans-serif' }}
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Text Chat
        </Link>
      </motion.div>
    </motion.div>
  );

  const renderEndedState = () => (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className="flex flex-col items-center justify-center h-full"
    >
      <div className="text-center mb-8">
        <h2 className="text-4xl font-black text-transparent bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text mb-4 tracking-tight" style={{ fontFamily: 'Inter, sans-serif' }}>Call Ended</h2>
        <p className="text-gray-300 mb-8 text-lg font-medium" style={{ fontFamily: 'Inter, sans-serif' }}>
          Duration: {formatDuration(callDuration)}
        </p>
        
        <div className="flex gap-4">
          <Button
            size="lg"
            onClick={startCall}
            className="bg-green-500 hover:bg-green-600"
          >
            <Phone className="w-5 h-5 mr-2" />
            Call Again
          </Button>
          
          <Link to="/chat">
            <Button variant="outline" size="lg">
              Back to Chat
            </Button>
          </Link>
        </div>
      </div>
    </motion.div>
  );

  const renderActiveCall = () => (
    <div className="h-full flex flex-col">
      {/* Header */}
      <motion.div
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex items-center justify-between p-6 backdrop-blur-xl bg-black/30 border-b border-white/20 shadow-2xl"
      >
        <div className="flex items-center gap-4">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.2 }}
          >
            <Badge className={`${getCallStateColor(callState)} text-white px-4 py-2 text-sm font-bold shadow-lg`} style={{ fontFamily: 'Inter, sans-serif' }}>
              <div className="flex items-center gap-2">
                <motion.div 
                  className="w-2 h-2 bg-white rounded-full"
                  animate={{ 
                    scale: callState === 'live' ? [1, 1.5, 1] : 1,
                    opacity: callState === 'live' ? [1, 0.5, 1] : 1
                  }}
                  transition={{ 
                    duration: 1.5, 
                    repeat: callState === 'live' ? Infinity : 0 
                  }}
                />
                {getCallStateText(callState)}
              </div>
            </Badge>
          </motion.div>
          
          {callState === 'live' && (
            <motion.div 
              className="flex items-center gap-6 text-white"
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: 0.4 }}
            >
              <div className="flex items-center gap-2 bg-white/10 backdrop-blur-md px-3 py-2 rounded-full border border-white/20">
                <Timer className="w-4 h-4 text-emerald-400" />
                <span className="font-mono text-lg font-black tracking-wider text-emerald-300" style={{ fontFamily: 'JetBrains Mono, monospace' }}>
                  {formatDuration(callDuration)}
                </span>
              </div>
              
              <div className="flex items-center gap-2 bg-white/10 backdrop-blur-md px-3 py-2 rounded-full border border-white/20">
                {latency !== null ? (
                  <>
                    <motion.div
                      animate={{
                        scale: [1, 1.2, 1],
                        opacity: [1, 0.7, 1]
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity
                      }}
                    >
                      <Wifi className="w-4 h-4 text-emerald-400" />
                    </motion.div>
                    <span className="text-sm font-bold text-emerald-300" style={{ fontFamily: 'JetBrains Mono, monospace' }}>{latency}ms</span>
                  </>
                ) : (
                  <>
                    <WifiOff className="w-4 h-4 text-red-400" />
                    <span className="text-sm text-red-300">Offline</span>
                  </>
                )}
              </div>
            </motion.div>
          )}
        </div>

        <motion.div
          initial={{ x: 20, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ delay: 0.3 }}
        >
          <Link to="/chat">
            <Button 
              variant="ghost" 
              size="sm" 
              className="text-white hover:bg-white/10 backdrop-blur-md border border-white/20 transition-all duration-200"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Chat
            </Button>
          </Link>
        </motion.div>
      </motion.div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Left: Live Captions */}
        {captionsEnabled && (
          <motion.div
            initial={{ x: -100, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            className="w-1/3 p-6 bg-black/20 backdrop-blur-sm"
          >
            <h3 className="text-white font-bold mb-4 text-lg tracking-wide" style={{ fontFamily: 'Inter, sans-serif' }}>Live Captions</h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              <AnimatePresence>
                {captions.slice(-10).map((caption) => (
                  <CaptionItem key={caption.id} caption={caption} />
                ))}
              </AnimatePresence>
            </div>
          </motion.div>
        )}

        {/* Center: Call Card */}
        <div className="flex-1 flex items-center justify-center p-8">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-center"
          >
            {/* Bot Avatar with Pulsing Ring */}
            <div className="relative mb-8">
              {/* Outer pulsing ring */}
              <motion.div
                animate={{
                  scale: callState === 'live' && (isRecording || isPTTActive) ? [1, 1.4, 1] : [1, 1.1, 1],
                  opacity: callState === 'live' && (isRecording || isPTTActive) ? [0.5, 0.2, 0.5] : [0.3, 0.1, 0.3]
                }}
                transition={{
                  duration: callState === 'live' && (isRecording || isPTTActive) ? 1.5 : 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
                className="absolute inset-0 rounded-full bg-gradient-to-r from-emerald-400 to-cyan-400 blur-xl"
              />
              
              {/* Middle ring */}
              <motion.div
                animate={{
                  scale: callState === 'live' && (isRecording || isPTTActive) ? [1, 1.25, 1] : [1, 1.05, 1],
                  opacity: [0.4, 0.8, 0.4]
                }}
                transition={{
                  duration: callState === 'live' && (isRecording || isPTTActive) ? 2 : 4,
                  repeat: Infinity,
                  ease: "easeInOut",
                  delay: 0.5
                }}
                className="absolute inset-2 rounded-full bg-gradient-to-r from-blue-400 to-purple-400 blur-lg"
              />
              
              {/* Avatar container with gradient border */}
              <motion.div
                animate={{
                  rotate: [0, 360]
                }}
                transition={{
                  duration: 20,
                  repeat: Infinity,
                  ease: "linear"
                }}
                className="absolute inset-4 rounded-full bg-gradient-to-r from-emerald-400 via-blue-400 to-purple-400 p-1"
              >
                <div className="w-full h-full rounded-full bg-slate-900">
                  <Avatar className="w-full h-full relative z-10 border-4 border-white/20">
                    <AvatarFallback className="bg-gradient-to-br from-emerald-500 via-blue-500 to-purple-600 text-white text-4xl relative overflow-hidden">
                      {/* Animated sparkles */}
                      <motion.div
                        animate={{
                          scale: [1, 1.1, 1],
                          rotate: [0, 10, -10, 0]
                        }}
                        transition={{
                          duration: 3,
                          repeat: Infinity,
                          ease: "easeInOut"
                        }}
                      >
                        <Bot className="w-16 h-16 relative z-10" />
                      </motion.div>
                      
                      {/* Floating sparkles */}
                      <motion.div
                        className="absolute top-2 right-2 w-2 h-2 bg-white rounded-full"
                        animate={{
                          opacity: [0, 1, 0],
                          scale: [0.5, 1, 0.5]
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          delay: 0.5
                        }}
                      />
                      <motion.div
                        className="absolute bottom-3 left-3 w-1 h-1 bg-white rounded-full"
                        animate={{
                          opacity: [0, 1, 0],
                          scale: [0.5, 1, 0.5]
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          delay: 1.5
                        }}
                      />
                    </AvatarFallback>
                  </Avatar>
                </div>
              </motion.div>
            </div>

            <h2 className="text-3xl font-black text-transparent bg-gradient-to-r from-emerald-400 via-blue-400 to-purple-400 bg-clip-text mb-2 tracking-tight" style={{ fontFamily: 'Inter, sans-serif' }}>
              Campus AI Assistant
            </h2>
            <p className="text-gray-300 mb-8 text-lg font-medium" style={{ fontFamily: 'Inter, sans-serif' }}>
              {callState === 'connecting' 
                ? 'Connecting to assistant...' 
                : 'Ready to help with your questions'
              }
            </p>

            {/* Voice Visualizer */}
            <VoiceVisualizer
              stream={stream}
              isActive={callState === 'live' && (isRecording || isPTTActive)}
              className="mb-8"
            />
          </motion.div>
        </div>

        {/* Right: History */}
        <motion.div
          initial={{ x: 100, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="w-1/4 p-6 bg-black/20 backdrop-blur-sm"
        >
          <h3 className="text-white font-bold mb-4 text-lg tracking-wide" style={{ fontFamily: 'Inter, sans-serif' }}>Recent History</h3>
          <div className="space-y-3">
            {history.slice(-5).map((item) => (
              <HistoryItem key={item.id} item={item} />
            ))}
          </div>
        </motion.div>
      </div>

      {/* Controls */}
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="p-6 flex justify-center"
      >
        <CallControls
          isMuted={isMuted}
          isPTTActive={isPTTActive}
          captionsEnabled={captionsEnabled}
          autoTTSEnabled={autoTTSEnabled}
          isRecording={isRecording}
          onToggleMute={toggleMute}
          onTogglePTT={togglePTT}
          onToggleCaptions={toggleCaptions}
          onToggleAutoTTS={toggleAutoTTS}
          onEndCall={endCall}
          disabled={callState !== 'live'}
        />
      </motion.div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-950 via-purple-950 to-slate-950 flex flex-col overflow-hidden relative">
      {/* Animated Background */}
      <div className="absolute inset-0">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-purple-600/10 to-cyan-600/10 animate-pulse" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(120,119,198,0.3),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(59,130,246,0.2),transparent_50%)]" />
        
        {/* Floating particles */}
        <motion.div
          className="absolute top-1/4 left-1/4 w-2 h-2 bg-blue-400/30 rounded-full"
          animate={{
            y: [-20, 20, -20],
            x: [-10, 10, -10],
            opacity: [0.3, 0.7, 0.3]
          }}
          transition={{ duration: 6, repeat: Infinity }}
        />
        <motion.div
          className="absolute top-3/4 right-1/3 w-3 h-3 bg-purple-400/20 rounded-full"
          animate={{
            y: [20, -20, 20],
            x: [10, -10, 10],
            opacity: [0.2, 0.6, 0.2]
          }}
          transition={{ duration: 8, repeat: Infinity, delay: 2 }}
        />
        <motion.div
          className="absolute top-1/2 right-1/4 w-1 h-1 bg-cyan-400/40 rounded-full"
          animate={{
            y: [-30, 30, -30],
            opacity: [0.4, 0.8, 0.4]
          }}
          transition={{ duration: 4, repeat: Infinity, delay: 1 }}
        />
      </div>
      
      <div className="relative z-10 flex flex-col min-h-screen">
        <AnimatePresence mode="wait">
          {callState === 'idle' && renderIdleState()}
          {callState === 'ended' && renderEndedState()}
          {(callState === 'connecting' || callState === 'live' || callState === 'ending') && renderActiveCall()}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default CallPage;
