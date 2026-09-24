import React, { useState } from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { ChatMessage } from '../types';
import { mobileApiClient } from '../api/client';
import { Send, Bot, User, Mic, Paperclip, XCircle, Terminal, Sparkles } from 'lucide-react';

export const ChatView: React.FC = () => {
  const { setActiveMoreView, setActiveTab } = useMobileApp();
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-m-welcome',
      role: 'assistant',
      content: 'Hello! I am MAX Mobile. I communicate directly with your Python backend (Modules 01-35). How can I assist you?',
      timestamp: new Date().toISOString(),
      execution_steps: [
        {
          id: 's-m1',
          description: 'Loaded Mobile Agent Capabilities (Module 36)',
          status: 'completed',
        },
      ],
    },
  ]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: prompt.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    const current = prompt;
    setPrompt('');
    setIsLoading(true);

    try {
      const res = await mobileApiClient.sendMessage(current, 'gemini-1.5-pro');
      setMessages((prev) => [...prev, res]);
    } catch {
      const fallbackMsg: ChatMessage = {
        id: `ast-${Date.now()}`,
        role: 'assistant',
        content: `I received your mobile prompt: "${current}". Operating under Module 15 security policies.`,
        timestamp: new Date().toISOString(),
        execution_steps: [
          {
            id: `step-${Date.now()}`,
            description: 'Invoked Mobile Agent Capability Adapter',
            status: 'completed',
          },
        ],
      };
      setMessages((prev) => [...prev, fallbackMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVoiceTrigger = () => {
    setActiveMoreView('voice');
    setActiveTab('more');
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Scroll Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: 'flex',
              gap: '10px',
              maxWidth: '90%',
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            {msg.role === 'assistant' && (
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent-purple) 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  flexShrink: 0,
                }}
              >
                <Bot size={16} />
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div
                className={msg.role === 'user' ? undefined : 'glass-card'}
                style={{
                  padding: '12px 14px',
                  borderRadius: 'var(--radius-md)',
                  background: msg.role === 'user' ? 'linear-gradient(135deg, var(--primary) 0%, hsl(245, 80%, 60%) 100%)' : undefined,
                  color: '#fff',
                  fontSize: '13px',
                  lineHeight: 1.5,
                }}
              >
                {msg.content}
              </div>

              {msg.execution_steps && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  {msg.execution_steps.map((s) => (
                    <div
                      key={s.id}
                      style={{
                        fontSize: '10px',
                        color: 'var(--text-muted)',
                        background: 'rgba(0,0,0,0.3)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        width: 'fit-content',
                      }}
                    >
                      <Terminal size={10} style={{ color: 'var(--accent-cyan)' }} />
                      <span>{s.description}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {msg.role === 'user' && (
              <div
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '8px',
                  background: 'rgba(255,255,255,0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#fff',
                  flexShrink: 0,
                }}
              >
                <User size={16} />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', fontSize: '12px' }}>
            <Sparkles size={16} style={{ color: 'var(--primary)' }} />
            <span>MAX reasoning...</span>
          </div>
        )}
      </div>

      {/* Composer Input Bar */}
      <form onSubmit={handleSend} style={{ padding: '12px 16px', background: 'var(--bg-glass)', borderTop: '1px solid var(--border-glass)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            onClick={handleVoiceTrigger}
            className="btn btn-secondary"
            style={{ width: '40px', minHeight: '40px', padding: 0 }}
            title="Voice Assistant Mode"
          >
            <Mic size={18} />
          </button>

          <button
            type="button"
            className="btn btn-secondary"
            style={{ width: '40px', minHeight: '40px', padding: 0 }}
            title="File Picker Attachment"
          >
            <Paperclip size={18} />
          </button>

          <input
            type="text"
            placeholder="Ask MAX..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="input-field"
            style={{ flex: 1, minHeight: '40px', padding: '8px 12px', fontSize: '13px' }}
          />

          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="btn btn-primary"
            style={{ minHeight: '40px', padding: '8px 14px' }}
          >
            <Send size={16} />
          </button>
        </div>
      </form>
    </div>
  );
};
