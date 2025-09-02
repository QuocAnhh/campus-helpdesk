import { useState, useEffect, useCallback } from 'react';

export interface AudioDevice {
  deviceId: string;
  label: string;
  kind: 'audioinput' | 'audiooutput';
}

export const useDevices = () => {
  const [inputDevices, setInputDevices] = useState<AudioDevice[]>([]);
  const [outputDevices, setOutputDevices] = useState<AudioDevice[]>([]);
  const [selectedInput, setSelectedInput] = useState<string>('');
  const [selectedOutput, setSelectedOutput] = useState<string>('');
  const [permissionGranted, setPermissionGranted] = useState(false);

  const requestPermissions = useCallback(async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setPermissionGranted(true);
      return true;
    } catch (error) {
      console.error('Failed to get media permissions:', error);
      setPermissionGranted(false);
      return false;
    }
  }, []);

  const refreshDevices = useCallback(async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      
      const inputs = devices
        .filter(device => device.kind === 'audioinput')
        .map(device => ({
          deviceId: device.deviceId,
          label: device.label || `Microphone ${device.deviceId.slice(0, 8)}`,
          kind: 'audioinput' as const
        }));

      const outputs = devices
        .filter(device => device.kind === 'audiooutput')
        .map(device => ({
          deviceId: device.deviceId,
          label: device.label || `Speaker ${device.deviceId.slice(0, 8)}`,
          kind: 'audiooutput' as const
        }));

      setInputDevices(inputs);
      setOutputDevices(outputs);

      // Set default devices if none selected
      if (!selectedInput && inputs.length > 0) {
        setSelectedInput(inputs[0].deviceId);
      }
      if (!selectedOutput && outputs.length > 0) {
        setSelectedOutput(outputs[0].deviceId);
      }
    } catch (error) {
      console.error('Failed to enumerate devices:', error);
    }
  }, [selectedInput, selectedOutput]);

  const setAudioOutputDevice = useCallback(async (deviceId: string) => {
    setSelectedOutput(deviceId);
    // Note: Setting audio output device programmatically is limited in browsers
    // This mainly stores the preference for use with setSinkId on audio elements
  }, []);

  useEffect(() => {
    refreshDevices();
    
    // Listen for device changes
    navigator.mediaDevices.addEventListener('devicechange', refreshDevices);
    
    return () => {
      navigator.mediaDevices.removeEventListener('devicechange', refreshDevices);
    };
  }, [refreshDevices]);

  return {
    inputDevices,
    outputDevices,
    selectedInput,
    selectedOutput,
    permissionGranted,
    requestPermissions,
    refreshDevices,
    setSelectedInput,
    setSelectedOutput: setAudioOutputDevice,
  };
};
