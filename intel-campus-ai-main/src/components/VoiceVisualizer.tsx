import React, { useRef, useEffect, useState } from 'react';

interface VoiceVisualizerProps {
  stream?: MediaStream | null;
  isActive?: boolean;
  className?: string;
}

export const VoiceVisualizer: React.FC<VoiceVisualizerProps> = ({
  stream,
  isActive = false,
  className = ''
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationIdRef = useRef<number>();
  const analyserRef = useRef<AnalyserNode>();
  const dataArrayRef = useRef<Uint8Array>();

  useEffect(() => {
    if (!stream || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const canvasCtx = canvas.getContext('2d');
    if (!canvasCtx) return;

    // Set up audio context and analyser
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    
    source.connect(analyser);
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.8;
    
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    
    analyserRef.current = analyser;
    dataArrayRef.current = dataArray;

    const draw = () => {
      if (!isActive) {
        // Draw flat line when inactive
        canvasCtx.fillStyle = 'rgb(20, 20, 20)';
        canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
        
        canvasCtx.strokeStyle = 'rgb(59, 130, 246)';
        canvasCtx.lineWidth = 2;
        canvasCtx.beginPath();
        canvasCtx.moveTo(0, canvas.height / 2);
        canvasCtx.lineTo(canvas.width, canvas.height / 2);
        canvasCtx.stroke();
        
        animationIdRef.current = requestAnimationFrame(draw);
        return;
      }

      analyser.getByteFrequencyData(dataArray);

      canvasCtx.fillStyle = 'rgb(20, 20, 20)';
      canvasCtx.fillRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = (dataArray[i] / 255) * canvas.height;

        const red = (barHeight / canvas.height) * 255;
        const green = 100;
        const blue = 255 - red;

        canvasCtx.fillStyle = `rgb(${red},${green},${blue})`;
        canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

        x += barWidth + 1;
      }

      animationIdRef.current = requestAnimationFrame(draw);
    };

    draw();

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (audioContext.state !== 'closed') {
        audioContext.close();
      }
    };
  }, [stream, isActive]);

  // Simple animated bars fallback when no stream
  const [animatedBars, setAnimatedBars] = useState<number[]>([]);

  useEffect(() => {
    if (stream) return;

    const generateBars = () => {
      const bars = Array.from({ length: 32 }, () => Math.random() * 100);
      setAnimatedBars(bars);
    };

    let interval: NodeJS.Timeout;
    if (isActive) {
      generateBars();
      interval = setInterval(generateBars, 100);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [stream, isActive]);

  return (
    <div className={`relative ${className}`}>
      {stream ? (
        <canvas
          ref={canvasRef}
          width={300}
          height={80}
          className="w-full h-full rounded-lg bg-gray-900"
        />
      ) : (
        <div className="flex items-end justify-center gap-1 h-20 bg-gray-900 rounded-lg p-2">
          {animatedBars.map((height, index) => (
            <div
              key={index}
              className="bg-gradient-to-t from-blue-500 to-blue-300 w-2 rounded-sm transition-all duration-100"
              style={{
                height: isActive ? `${Math.max(height, 10)}%` : '20%',
                opacity: isActive ? 1 : 0.3
              }}
            />
          ))}
        </div>
      )}
    </div>
  );
};
