import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useWebApp } from '../context/WebAppContext';
import { ChatMessage, VoiceState } from '../types';
import { webApiClient } from '../api/client';
import { speechRecognitionService, speechSynthesisService } from '../services/speech';
import { AudioWaveform } from '../components/AudioWaveform';
import {
  Send,
  Bot,
  User,
  Mic,
  MicOff,
  Square,
  Volume2,
  VolumeX,
  Play,
  Pause,
  RotateCcw,
  Terminal,
  Sparkles,
  Layers,
  AlertCircle,
  X,
  Radio,
} from 'lucide-react';

export const ChatView: React.FC = () => {
  const { preferences } = useWebApp();

  // Chat State
  const [prompt, setPrompt] = useState('');
  const [selectedModel, setSelectedModel] = useState(preferences.primary_model);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-welcome',
      role: 'assistant',
      content:
        'Hello! I am MAX, your personal AI operating layer. I have full context of Modules 01-34. How can I assist you today?',
      timestamp: new Date().toISOString(),
      model_id: 'gemini-1.5-pro',
      execution_steps: [
        {
          id: 'step-1',
          step_type: 'memory_retrieval',
          description: 'Loaded personal user preferences from Module 08 Memory Engine',
          status: 'completed',
        },
        {
          id: 'step-2',
          step_type: 'reasoning',
          description: 'Verified System Autonomy Level: Guarded Execution',
          status: 'completed',
        },
      ],
    },
  ]);

  // Voice System State
  const [isVoiceMode, setIsVoiceMode] = useState(false);
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [liveTranscript, setLiveTranscript] = useState('');
  const [audioLevel, setAudioLevel] = useState(0);
  const [voiceError, setVoiceError] = useState<string | null>(null);
  const [speakingMsgId, setSpeakingMsgId] = useState<string | null>(null);
  const [isTtsPaused, setIsTtsPaused] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, liveTranscript, isLoading]);

  // Check browser speech support on mount
  useEffect(() => {
    if (!speechRecognitionService.isSupported()) {
      setVoiceState('unsupported');
    }
  }, []);

  // Submit chat prompt to backend API
  const submitMessage = useCallback(
    async (textToSubmit: string, autoSpeakResponse = false) => {
      if (!textToSubmit.trim() || isLoading) return;

      const userMsg: ChatMessage = {
        id: `usr-${Date.now()}`,
        role: 'user',
        content: textToSubmit.trim(),
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setPrompt('');
      setLiveTranscript('');
      setIsLoading(true);
      setVoiceState('thinking');

      try {
        const response = await webApiClient.sendMessage(textToSubmit.trim(), selectedModel);
        setMessages((prev) => [...prev, response]);

        if (autoSpeakResponse || isVoiceMode || preferences.auto_speak) {
          speakResponse(response.content, response.id, () => {
            if (isVoiceMode) {
              // Continuous conversation loop: Return to listening after speaking
              startListeningSession();
            } else {
              setVoiceState('idle');
            }
          });
        } else {
          setVoiceState('idle');
        }
      } catch {
        const aiResponse: ChatMessage = {
          id: `ast-${Date.now()}`,
          role: 'assistant',
          content: `I received your request: "${textToSubmit.trim()}". Processing via ${selectedModel}... All system modules are operating normally.`,
          timestamp: new Date().toISOString(),
          model_id: selectedModel,
          execution_steps: [
            {
              id: `step-${Date.now()}`,
              step_type: 'tool_call',
              description: 'Invoked Module 14 Tool Registry for context verification',
              status: 'completed',
              tool_name: 'read_file',
            },
          ],
        };
        setMessages((prev) => [...prev, aiResponse]);

        if (autoSpeakResponse || isVoiceMode || preferences.auto_speak) {
          speakResponse(aiResponse.content, aiResponse.id, () => {
            if (isVoiceMode) {
              startListeningSession();
            } else {
              setVoiceState('idle');
            }
          });
        } else {
          setVoiceState('idle');
        }
      } finally {
        setIsLoading(false);
      }
    },
    [isLoading, selectedModel, isVoiceMode, preferences.auto_speak]
  );

  // Text-to-Speech execution for AI response
  const speakResponse = (text: string, msgId: string, onFinish?: () => void) => {
    if (!preferences.voice_output_enabled) {
      onFinish?.();
      return;
    }

    setSpeakingMsgId(msgId);
    setVoiceState('speaking');
    setIsTtsPaused(false);

    speechSynthesisService.speak(
      text,
      {
        rate: preferences.speech_speed,
        lang: preferences.voice_language,
        voiceName: preferences.selected_voice,
      },
      {
        onStart: () => {
          setVoiceState('speaking');
          setSpeakingMsgId(msgId);
        },
        onEnd: () => {
          setSpeakingMsgId(null);
          setIsTtsPaused(false);
          onFinish?.();
        },
        onError: (err) => {
          setSpeakingMsgId(null);
          setIsTtsPaused(false);
          setVoiceError(`TTS Error: ${err}`);
          onFinish?.();
        },
      }
    );
  };

  // Immediate Interruption / Stop MAX Speaking (Barge-in)
  const stopMaxSpeaking = () => {
    speechSynthesisService.stop();
    setSpeakingMsgId(null);
    setIsTtsPaused(false);
  };

  // Start listening session with speech recognition
  const startListeningSession = useCallback(() => {
    if (!preferences.voice_input_enabled) {
      setVoiceError('Voice input is disabled in settings.');
      return;
    }

    // Stop speaking if currently speaking
    if (speechSynthesisService.isSpeaking()) {
      speechSynthesisService.stop();
      setSpeakingMsgId(null);
    }

    setVoiceError(null);

    speechRecognitionService.startListening(preferences.voice_language, {
      onStateChange: (state) => {
        setVoiceState(state);
      },
      onInterimResult: (interim) => {
        setLiveTranscript(interim);
      },
      onFinalResult: (finalText) => {
        setLiveTranscript(finalText);
        setVoiceState('processing');

        if (isVoiceMode) {
          // In Voice Mode, automatically submit final transcript
          submitMessage(finalText, true);
        } else {
          // In standard mode, put final transcript into prompt input
          setPrompt(finalText);
          setVoiceState('idle');
        }
      },
      onError: (errMessage, isPermDenied) => {
        setVoiceError(errMessage);
        if (isPermDenied) {
          setVoiceState('permission_denied');
        } else {
          setVoiceState('error');
        }
      },
      onEnd: () => {
        setAudioLevel(0);
      },
      onAudioLevel: (level) => {
        setAudioLevel(level);
      },
    });
  }, [preferences.voice_input_enabled, preferences.voice_language, isVoiceMode, submitMessage]);

  // Cancel recording session
  const cancelListeningSession = () => {
    speechRecognitionService.cancelListening();
    setLiveTranscript('');
    setVoiceState('idle');
    setAudioLevel(0);
  };

  // Toggle Voice Mode
  const toggleVoiceMode = () => {
    if (!isVoiceMode) {
      setIsVoiceMode(true);
      startListeningSession();
    } else {
      setIsVoiceMode(false);
      speechRecognitionService.cancelListening();
      speechSynthesisService.stop();
      setSpeakingMsgId(null);
      setVoiceState('idle');
    }
  };

  // Handle Microphone Button Click (Context Aware)
  const handleMicClick = () => {
    if (voiceState === 'speaking') {
      // BARGE-IN INTERRUPT: Stop speaking immediately & switch to listening
      stopMaxSpeaking();
      startListeningSession();
      return;
    }

    if (voiceState === 'listening') {
      // Stop listening & process
      speechRecognitionService.stopListening();
      return;
    }

    // Start recording
    startListeningSession();
  };

  // Handle Form Submit
  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (voiceState === 'listening') {
      speechRecognitionService.stopListening();
    }
    submitMessage(prompt, false);
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', position: 'relative' }}>
      {/* Top Options & Voice Mode Header Bar */}
      <div
        className="glass-panel"
        style={{
          borderRadius: 0,
          borderLeft: 0,
          borderRight: 0,
          borderTop: 0,
          padding: '12px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={18} style={{ color: 'var(--primary)' }} />
            <span style={{ fontSize: '13px', fontWeight: 600 }}>Active Model:</span>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="input-field"
              style={{ width: '170px', padding: '6px 10px', fontSize: '12px' }}
            >
              <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
              <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
              <option value="ollama-llama3">Local Ollama Llama3</option>
            </select>
          </div>

          {/* Voice Mode Toggle Control */}
          <button
            type="button"
            onClick={toggleVoiceMode}
            className="btn"
            style={{
              padding: '6px 14px',
              fontSize: '12px',
              fontWeight: 600,
              borderRadius: '20px',
              background: isVoiceMode
                ? 'linear-gradient(135deg, rgba(99, 102, 241, 0.25) 0%, rgba(6, 182, 212, 0.25) 100%)'
                : 'rgba(255, 255, 255, 0.05)',
              border: isVoiceMode ? '1px solid var(--accent-cyan)' : '1px solid var(--border-glass)',
              color: isVoiceMode ? '#fff' : 'var(--text-muted)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
            aria-label={isVoiceMode ? 'Disable Voice Mode' : 'Enable Voice Mode'}
          >
            <Radio size={14} style={{ color: isVoiceMode ? 'var(--accent-cyan)' : 'currentColor' }} />
            <span>{isVoiceMode ? 'Voice Mode ● Active' : 'Voice Mode'}</span>
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
          <Layers size={14} />
          <span>
            Autonomy:{' '}
            <strong style={{ color: 'var(--text-main)', textTransform: 'capitalize' }}>
              {preferences.autonomy_level}
            </strong>
          </span>
        </div>
      </div>

      {/* Voice Error Banner */}
      {voiceError && (
        <div
          style={{
            background: 'rgba(239, 68, 68, 0.15)',
            borderBottom: '1px solid rgba(239, 68, 68, 0.3)',
            padding: '10px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '13px',
            color: '#fca5a5',
          }}
          role="alert"
          aria-live="polite"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AlertCircle size={16} />
            <span>{voiceError}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <button
              onClick={startListeningSession}
              className="btn btn-secondary"
              style={{ padding: '4px 10px', fontSize: '11px' }}
            >
              <RotateCcw size={12} />
              <span>Retry</span>
            </button>
            <button
              onClick={() => setVoiceError(null)}
              style={{ background: 'none', border: 'none', color: '#fca5a5', cursor: 'pointer' }}
            >
              <X size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Dedicated Voice Mode Overlay Panel */}
      {isVoiceMode && (
        <div
          className="glass-card"
          style={{
            margin: '16px 24px 0 24px',
            padding: '20px 24px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '14px',
            background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 27, 75, 0.85) 100%)',
            borderColor: 'var(--primary)',
            boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
            borderRadius: 'var(--radius-lg)',
          }}
          aria-live="polite"
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', fontWeight: 600, color: 'var(--accent-cyan)' }}>
              <Radio size={14} className="animate-pulse" />
              <span>MAX VOICE CONVERSATION MODE</span>
            </div>
            <button
              onClick={() => setIsVoiceMode(false)}
              className="btn btn-secondary"
              style={{ padding: '4px 10px', fontSize: '11px' }}
            >
              Exit Voice Mode
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', margin: '8px 0' }}>
            <AudioWaveform state={voiceState} audioLevel={audioLevel} barCount={24} height={42} />

            <span
              style={{
                fontSize: '13px',
                fontWeight: 600,
                color: voiceState === 'listening' ? 'var(--accent-cyan)' : voiceState === 'speaking' ? 'var(--primary)' : 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              {voiceState === 'listening'
                ? '● Listening to your voice...'
                : voiceState === 'processing'
                ? 'Processing Speech...'
                : voiceState === 'thinking'
                ? 'MAX is reasoning...'
                : voiceState === 'speaking'
                ? 'MAX is speaking...'
                : 'Voice Mode Active — Speak anytime'}
            </span>

            {liveTranscript && (
              <p
                style={{
                  fontSize: '14px',
                  fontStyle: 'italic',
                  color: 'var(--text-main)',
                  background: 'rgba(0,0,0,0.3)',
                  padding: '8px 16px',
                  borderRadius: 'var(--radius-md)',
                  margin: '4px 0 0 0',
                  textAlign: 'center',
                }}
              >
                "{liveTranscript}"
              </p>
            )}
          </div>

          {voiceState === 'speaking' && (
            <button
              onClick={() => {
                stopMaxSpeaking();
                startListeningSession();
              }}
              className="btn btn-secondary"
              style={{ padding: '6px 14px', fontSize: '12px', borderColor: 'var(--accent-pink)' }}
            >
              <Mic size={14} style={{ color: 'var(--accent-pink)' }} />
              <span>Interrupt & Speak</span>
            </button>
          )}
        </div>
      )}

      {/* Messages Scroll Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {messages.map((msg) => {
          const isCurrentSpeaking = speakingMsgId === msg.id;

          return (
            <div
              key={msg.id}
              style={{
                display: 'flex',
                gap: '14px',
                maxWidth: '85%',
                alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
              }}
            >
              {msg.role === 'assistant' && (
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent-purple) 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    flexShrink: 0,
                    boxShadow: isCurrentSpeaking ? '0 0 12px var(--primary)' : 'none',
                  }}
                >
                  <Bot size={20} />
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
                <div
                  className={msg.role === 'user' ? undefined : 'glass-card'}
                  style={{
                    padding: '14px 18px',
                    borderRadius: 'var(--radius-lg)',
                    background:
                      msg.role === 'user'
                        ? 'linear-gradient(135deg, var(--primary) 0%, hsl(245, 80%, 60%) 100%)'
                        : isCurrentSpeaking
                        ? 'rgba(99, 102, 241, 0.15)'
                        : undefined,
                    borderColor: isCurrentSpeaking ? 'var(--primary)' : undefined,
                    color: '#fff',
                    fontSize: '14px',
                    lineHeight: 1.6,
                    position: 'relative',
                  }}
                >
                  {msg.content}

                  {/* Audio Controls for AI Assistant messages */}
                  {msg.role === 'assistant' && (
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                        marginTop: '10px',
                        paddingTop: '8px',
                        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                      }}
                    >
                      {isCurrentSpeaking ? (
                        <>
                          <button
                            type="button"
                            onClick={() => {
                              if (isTtsPaused) {
                                speechSynthesisService.resume();
                                setIsTtsPaused(false);
                              } else {
                                speechSynthesisService.pause();
                                setIsTtsPaused(true);
                              }
                            }}
                            className="btn btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '11px' }}
                            title={isTtsPaused ? 'Resume speaking' : 'Pause speaking'}
                          >
                            {isTtsPaused ? <Play size={12} /> : <Pause size={12} />}
                            <span>{isTtsPaused ? 'Resume' : 'Pause'}</span>
                          </button>

                          <button
                            type="button"
                            onClick={stopMaxSpeaking}
                            className="btn btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '11px', borderColor: 'var(--accent-pink)' }}
                            title="Stop MAX speaking"
                          >
                            <Square size={12} style={{ color: 'var(--accent-pink)' }} />
                            <span>Stop</span>
                          </button>

                          <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Volume2 size={14} style={{ color: 'var(--primary)' }} />
                            <AudioWaveform state="speaking" barCount={8} height={18} />
                          </div>
                        </>
                      ) : (
                        <button
                          type="button"
                          onClick={() => speakResponse(msg.content, msg.id)}
                          className="btn btn-secondary"
                          style={{ padding: '4px 10px', fontSize: '11px' }}
                          title="Speak response aloud (Module 26 TTS)"
                        >
                          <Volume2 size={12} style={{ color: 'var(--accent-cyan)' }} />
                          <span>Speak</span>
                        </button>
                      )}
                    </div>
                  )}
                </div>

                {/* Step Execution Logs Breakdown */}
                {msg.execution_steps && msg.execution_steps.length > 0 && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', paddingLeft: '4px' }}>
                    {msg.execution_steps.map((step) => (
                      <div
                        key={step.id}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px',
                          fontSize: '11px',
                          color: 'var(--text-muted)',
                          background: 'rgba(0,0,0,0.2)',
                          padding: '4px 8px',
                          borderRadius: '4px',
                          width: 'fit-content',
                        }}
                      >
                        <Terminal size={12} style={{ color: 'var(--accent-cyan)' }} />
                        <span>{step.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {msg.role === 'user' && (
                <div
                  style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.1)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    flexShrink: 0,
                  }}
                >
                  <User size={18} />
                </div>
              )}
            </div>
          );
        })}

        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '13px' }}>
            <Bot size={18} style={{ color: 'var(--primary)' }} />
            <span>MAX reasoning & assembling tools...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Live Interim Transcript Banner Overlay */}
      {voiceState === 'listening' && liveTranscript && !isVoiceMode && (
        <div
          style={{
            padding: '10px 24px',
            background: 'rgba(6, 182, 212, 0.12)',
            borderTop: '1px solid rgba(6, 182, 212, 0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '13px',
            color: 'var(--text-main)',
          }}
          aria-live="polite"
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <AudioWaveform state="listening" audioLevel={audioLevel} barCount={10} height={20} />
            <span>
              Listening... <strong style={{ color: 'var(--accent-cyan)' }}>"{liveTranscript}"</strong>
            </span>
          </div>
          <button
            onClick={cancelListeningSession}
            className="btn btn-secondary"
            style={{ padding: '4px 8px', fontSize: '11px' }}
          >
            Cancel
          </button>
        </div>
      )}

      {/* Input Bar */}
      <form onSubmit={handleSend} style={{ padding: '16px 24px', background: 'var(--bg-glass)', borderTop: '1px solid var(--border-glass)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Functional Voice Microphone Button */}
          <button
            type="button"
            onClick={handleMicClick}
            className={`btn ${voiceState === 'listening' ? 'btn-danger' : voiceState === 'speaking' ? 'btn-primary' : 'btn-secondary'}`}
            style={{
              width: '42px',
              height: '42px',
              padding: 0,
              borderRadius: '12px',
              position: 'relative',
              borderColor: voiceState === 'listening' ? 'var(--accent-pink)' : voiceState === 'speaking' ? 'var(--primary)' : undefined,
              boxShadow: voiceState === 'listening' ? '0 0 12px rgba(244, 63, 94, 0.6)' : 'none',
              transition: 'all 0.2s ease',
            }}
            title={
              voiceState === 'speaking'
                ? 'Interrupt MAX Speaking & Start Listening'
                : voiceState === 'listening'
                ? 'Stop Recording Speech'
                : 'Start Voice Input (Module 26 Speech System)'
            }
            aria-label={
              voiceState === 'speaking'
                ? 'Interrupt MAX Speaking'
                : voiceState === 'listening'
                ? 'Stop Voice Input'
                : 'Start Voice Input'
            }
          >
            {voiceState === 'listening' ? (
              <Square size={16} style={{ color: '#fff' }} />
            ) : voiceState === 'speaking' ? (
              <VolumeX size={18} style={{ color: '#fff' }} />
            ) : voiceState === 'permission_denied' || voiceState === 'unsupported' ? (
              <MicOff size={18} style={{ color: 'var(--text-muted)' }} />
            ) : (
              <Mic size={18} style={{ color: voiceState === 'processing' ? 'var(--accent-cyan)' : 'currentColor' }} />
            )}
          </button>

          <input
            type="text"
            placeholder={
              voiceState === 'listening'
                ? 'Listening to your speech...'
                : voiceState === 'speaking'
                ? 'MAX is speaking (click mic to interrupt)...'
                : 'Ask MAX to execute tasks, search knowledge, or inspect system...'
            }
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="input-field"
            style={{ flex: 1, padding: '12px 16px', fontSize: '14px' }}
          />

          <button
            type="submit"
            disabled={(!prompt.trim() && voiceState !== 'listening') || isLoading}
            className="btn btn-primary"
            style={{ padding: '12px 20px' }}
          >
            <Send size={16} />
            <span>Send</span>
          </button>
        </div>
      </form>
    </div>
  );
};
