import React, { useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { 
  Mic, 
  MicOff, 
  PhoneOff, 
  Settings, 
  Type, 
  Volume2, 
  VolumeX,
  Headphones
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useDevices } from '@/hooks/useDevices';

interface CallControlsProps {
  isMuted: boolean;
  isPTTActive: boolean;
  captionsEnabled: boolean;
  autoTTSEnabled: boolean;
  isRecording: boolean;
  onToggleMute: () => void;
  onTogglePTT: (active: boolean) => void;
  onToggleCaptions: () => void;
  onToggleAutoTTS: () => void;
  onEndCall: () => void;
  disabled?: boolean;
}

export const CallControls: React.FC<CallControlsProps> = ({
  isMuted,
  isPTTActive,
  captionsEnabled,
  autoTTSEnabled,
  isRecording,
  onToggleMute,
  onTogglePTT,
  onToggleCaptions,
  onToggleAutoTTS,
  onEndCall,
  disabled = false
}) => {
  const { inputDevices, outputDevices, selectedInput, selectedOutput, setSelectedInput, setSelectedOutput } = useDevices();

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (disabled) return;

      switch (event.key.toLowerCase()) {
        case 'm':
          if (!event.ctrlKey && !event.altKey) {
            event.preventDefault();
            onToggleMute();
          }
          break;
        case ' ':
          event.preventDefault();
          onTogglePTT(true);
          break;
        case 'escape':
          event.preventDefault();
          onEndCall();
          break;
      }
    };

    const handleKeyUp = (event: KeyboardEvent) => {
      if (disabled) return;

      if (event.key === ' ') {
        event.preventDefault();
        onTogglePTT(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('keyup', handleKeyUp);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('keyup', handleKeyUp);
    };
  }, [disabled, onToggleMute, onTogglePTT, onEndCall]);

  const handlePTTMouseDown = useCallback(() => {
    if (!disabled) onTogglePTT(true);
  }, [disabled, onTogglePTT]);

  const handlePTTMouseUp = useCallback(() => {
    if (!disabled) onTogglePTT(false);
  }, [disabled, onTogglePTT]);

  const controlVariants = {
    enabled: { scale: 1, opacity: 1 },
    disabled: { scale: 0.8, opacity: 0.5 },
    active: { scale: 1.1, opacity: 1 }
  };

  return (
    <TooltipProvider>
      <motion.div 
        className="flex items-center justify-center gap-4 p-6 bg-white/10 backdrop-blur-md rounded-2xl border border-white/20"
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3 }}
      >
        {/* Mute/Unmute */}
        <Tooltip>
          <TooltipTrigger asChild>
            <motion.div
              variants={controlVariants}
              animate={disabled ? 'disabled' : (isMuted ? 'active' : 'enabled')}
            >
              <Button
                variant={isMuted ? 'destructive' : 'secondary'}
                size="lg"
                className="w-16 h-16 rounded-full"
                onClick={onToggleMute}
                disabled={disabled}
              >
                {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
              </Button>
            </motion.div>
          </TooltipTrigger>
          <TooltipContent>
            <p>{isMuted ? 'Unmute' : 'Mute'} (M)</p>
          </TooltipContent>
        </Tooltip>

        {/* Push to Talk */}
        <Tooltip>
          <TooltipTrigger asChild>
            <motion.div
              variants={controlVariants}
              animate={disabled ? 'disabled' : (isPTTActive || isRecording ? 'active' : 'enabled')}
            >
              <Button
                variant={isPTTActive || isRecording ? 'default' : 'outline'}
                size="lg"
                className="w-20 h-16 rounded-full"
                onMouseDown={handlePTTMouseDown}
                onMouseUp={handlePTTMouseUp}
                onMouseLeave={handlePTTMouseUp}
                disabled={disabled}
              >
                <div className="flex flex-col items-center gap-1">
                  <Mic className={`w-5 h-5 ${(isPTTActive || isRecording) ? 'text-white' : ''}`} />
                  <span className="text-xs">PTT</span>
                </div>
              </Button>
            </motion.div>
          </TooltipTrigger>
          <TooltipContent>
            <p>Push to Talk (Space)</p>
          </TooltipContent>
        </Tooltip>

        {/* Device Selection */}
        <Tooltip>
          <TooltipTrigger asChild>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <motion.div
                  variants={controlVariants}
                  animate={disabled ? 'disabled' : 'enabled'}
                >
                  <Button
                    variant="outline"
                    size="lg"
                    className="w-16 h-16 rounded-full"
                    disabled={disabled}
                  >
                    <Headphones className="w-6 h-6" />
                  </Button>
                </motion.div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="center" className="w-64">
                <div className="p-2">
                  <div className="font-semibold text-sm mb-2">Microphone</div>
                  {inputDevices.map((device) => (
                    <DropdownMenuItem
                      key={device.deviceId}
                      onClick={() => setSelectedInput(device.deviceId)}
                      className={selectedInput === device.deviceId ? 'bg-primary/10' : ''}
                    >
                      {device.label}
                    </DropdownMenuItem>
                  ))}
                  
                  <div className="font-semibold text-sm mb-2 mt-4">Speaker</div>
                  {outputDevices.map((device) => (
                    <DropdownMenuItem
                      key={device.deviceId}
                      onClick={() => setSelectedOutput(device.deviceId)}
                      className={selectedOutput === device.deviceId ? 'bg-primary/10' : ''}
                    >
                      {device.label}
                    </DropdownMenuItem>
                  ))}
                </div>
              </DropdownMenuContent>
            </DropdownMenu>
          </TooltipTrigger>
          <TooltipContent>
            <p>Audio Devices</p>
          </TooltipContent>
        </Tooltip>

        {/* Captions Toggle */}
        <Tooltip>
          <TooltipTrigger asChild>
            <motion.div
              variants={controlVariants}
              animate={disabled ? 'disabled' : (captionsEnabled ? 'active' : 'enabled')}
            >
              <Button
                variant={captionsEnabled ? 'default' : 'outline'}
                size="lg"
                className="w-16 h-16 rounded-full"
                onClick={onToggleCaptions}
                disabled={disabled}
              >
                <Type className="w-6 h-6" />
              </Button>
            </motion.div>
          </TooltipTrigger>
          <TooltipContent>
            <p>Captions {captionsEnabled ? 'On' : 'Off'}</p>
          </TooltipContent>
        </Tooltip>

        {/* Auto-TTS Toggle */}
        <Tooltip>
          <TooltipTrigger asChild>
            <motion.div
              variants={controlVariants}
              animate={disabled ? 'disabled' : (autoTTSEnabled ? 'active' : 'enabled')}
            >
              <Button
                variant={autoTTSEnabled ? 'default' : 'outline'}
                size="lg"
                className="w-16 h-16 rounded-full"
                onClick={onToggleAutoTTS}
                disabled={disabled}
              >
                {autoTTSEnabled ? <Volume2 className="w-6 h-6" /> : <VolumeX className="w-6 h-6" />}
              </Button>
            </motion.div>
          </TooltipTrigger>
          <TooltipContent>
            <p>Auto-TTS {autoTTSEnabled ? 'On' : 'Off'}</p>
          </TooltipContent>
        </Tooltip>

        {/* End Call */}
        <Tooltip>
          <TooltipTrigger asChild>
            <motion.div
              variants={controlVariants}
              animate={disabled ? 'disabled' : 'enabled'}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                variant="destructive"
                size="lg"
                className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600"
                onClick={onEndCall}
                disabled={disabled}
              >
                <PhoneOff className="w-6 h-6" />
              </Button>
            </motion.div>
          </TooltipTrigger>
          <TooltipContent>
            <p>End Call (Esc)</p>
          </TooltipContent>
        </Tooltip>
      </motion.div>
    </TooltipProvider>
  );
};
