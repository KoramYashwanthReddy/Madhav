import React from 'react';
import { VoiceState } from '../types';

interface AudioWaveformProps {
  state: VoiceState;
  audioLevel?: number; // 0.0 to 1.0
  barCount?: number;
  height?: number;
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  state,
  audioLevel = 0,
  barCount = 16,
  height = 36,
}) => {
  const bars = Array.from({ length: barCount });

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '4px',
        height: `${height}px`,
        padding: '0 8px',
      }}
      aria-hidden="true"
    >
      {bars.map((_, index) => {
        let barHeightPercent = 20;

        if (state === 'listening') {
          // Calculate dynamic height based on position and real audio volume level
          const offset = Math.sin((index / barCount) * Math.PI);
          const levelMultiplier = Math.max(0.2, audioLevel);
          barHeightPercent = Math.min(100, Math.max(15, offset * levelMultiplier * 100));
        } else if (state === 'speaking') {
          // Dynamic sine wave animation pattern for MAX speaking
          const sine = Math.sin((index / barCount) * Math.PI * 2 + Date.now() / 200);
          barHeightPercent = Math.min(100, Math.max(25, (sine + 1.2) * 35));
        } else if (state === 'processing' || state === 'thinking') {
          // Wave pulse effect for thinking state
          const pulse = Math.sin((index + Date.now() / 150) * 0.5);
          barHeightPercent = Math.min(80, Math.max(20, (pulse + 1) * 35));
        } else {
          // Static minimal state
          const staticPattern = [20, 35, 50, 65, 80, 65, 50, 35, 20, 35, 50, 65, 50, 35, 20, 15];
          barHeightPercent = staticPattern[index % staticPattern.length] * 0.4;
        }

        const isHighlighted = state === 'listening' || state === 'speaking';

        return (
          <div
            key={index}
            style={{
              width: '3px',
              height: `${barHeightPercent}%`,
              borderRadius: '2px',
              backgroundColor: isHighlighted
                ? state === 'listening'
                  ? 'var(--accent-cyan)'
                  : 'var(--primary)'
                : 'rgba(255, 255, 255, 0.25)',
              boxShadow: isHighlighted
                ? state === 'listening'
                  ? '0 0 8px rgba(6, 182, 212, 0.6)'
                  : '0 0 8px rgba(99, 102, 241, 0.6)'
                : 'none',
              transition: state === 'listening' ? 'height 0.08s ease-out' : 'height 0.2s ease-in-out',
            }}
          />
        );
      })}
    </div>
  );
};
