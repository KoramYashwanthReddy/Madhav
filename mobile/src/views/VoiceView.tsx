import React, { useState, useEffect } from 'react';
import { voiceService } from '../services/VoiceService';
import { VoiceState } from '../types';
import { Mic, MicOff, Square, RefreshCw, Volume2, ShieldCheck, AlertCircle } from 'lucide-react';

export const VoiceView: React.FC = () => {
  const [voiceState, setVoiceState] = useState<VoiceState>('IDLE');
  const [transcript, setTranscript] = useState('');
  const [autoSpeak, setAutoSpeak] = useState(true);

  useEffect(() => {
    const unsubscribe = voiceService.subscribe((state, text) => {
      setVoiceState(state);
      if (text) setTranscript(text);
    });
    return unsubscribe;
  }, []);

  const handleStart = () => {
    voiceService.startListening();
  };

  const handleStop = () => {
    voiceService.stopListening();
  };

  const handleInterrupt = () => {
    voiceService.interruptSpeech();
  };

  return (
    <div className="mobile-view-container" style={{ alignItems: 'center', justifyContent: 'center', textAlign: 'center' }}>
      <div style={{ padding: '10px 16px', borderRadius: '999px', background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-glass)', fontSize: '12px', display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
        <ShieldCheck size={14} style={{ color: 'var(--status-online)' }} />
        <span>Module 26 Speech System</span>
      </div>

      <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '22px', fontWeight: 800, margin: '8px 0 4px 0' }}>
        Voice Assistant Mode
      </h2>
      <p style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '300px' }}>
        Explicit microphone capture & real-time text-to-speech interaction.
      </p>

      {/* State Visualizer Circle */}
      <div style={{ margin: '30px 0' }}>
        <div
          onClick={voiceState === 'LISTENING' ? handleStop : handleStart}
          style={{
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            background:
              voiceState === 'LISTENING' || voiceState === 'TRANSCRIBING'
                ? 'radial-gradient(circle, var(--status-danger) 0%, rgba(239, 68, 68, 0.4) 100%)'
                : voiceState === 'SPEAKING'
                ? 'radial-gradient(circle, var(--accent-purple) 0%, rgba(168, 85, 247, 0.4) 100%)'
                : 'radial-gradient(circle, var(--primary) 0%, rgba(99, 102, 241, 0.3) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            cursor: 'pointer',
            boxShadow:
              voiceState === 'LISTENING'
                ? '0 0 30px var(--status-danger)'
                : '0 0 25px var(--primary-glow)',
            transition: 'all 300ms ease',
          }}
        >
          {voiceState === 'LISTENING' ? (
            <Mic size={48} style={{ animation: 'pulse 1.5s infinite' }} />
          ) : voiceState === 'SPEAKING' ? (
            <Volume2 size={48} />
          ) : (
            <MicOff size={48} />
          )}
        </div>
      </div>

      {/* Current State Indicator */}
      <div style={{ fontSize: '14px', fontWeight: 700, color: 'var(--text-main)', letterSpacing: '0.5px' }}>
        STATE: <span style={{ color: 'var(--accent-cyan)' }}>{voiceState}</span>
      </div>

      {/* Live Transcript Display */}
      {transcript && (
        <div className="glass-card" style={{ padding: '14px', marginTop: '12px', width: '100%', maxWidth: '340px', fontSize: '13px', color: 'var(--text-muted)' }}>
          "{transcript}"
        </div>
      )}

      {/* Voice Controls */}
      <div style={{ display: 'flex', gap: '10px', marginTop: '24px' }}>
        {voiceState === 'LISTENING' ? (
          <button onClick={handleStop} className="btn btn-danger">
            <Square size={16} />
            <span>Stop Listening</span>
          </button>
        ) : voiceState === 'SPEAKING' ? (
          <button onClick={handleInterrupt} className="btn btn-secondary">
            <Square size={16} />
            <span>Interrupt</span>
          </button>
        ) : (
          <button onClick={handleStart} className="btn btn-primary">
            <Mic size={16} />
            <span>Start Voice</span>
          </button>
        )}
      </div>
    </div>
  );
};
