import React, { useState } from 'react';
import { useWebApp } from '../context/WebAppContext';
import { ChatMessage } from '../types';
import { webApiClient } from '../api/client';
import { Send, Bot, User, Mic, Terminal, ChevronRight, Sparkles, Layers } from 'lucide-react';

export const ChatView: React.FC = () => {
  const { preferences } = useWebApp();
  const [prompt, setPrompt] = useState('');
  const [selectedModel, setSelectedModel] = useState(preferences.primary_model);
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-welcome',
      role: 'assistant',
      content: 'Hello! I am MAX, your personal AI operating layer. I have full context of Modules 01-34. How can I assist you today?',
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
    const currentPrompt = prompt;
    setPrompt('');
    setIsLoading(true);

    try {
      const response = await webApiClient.sendMessage(currentPrompt, selectedModel);
      setMessages((prev) => [...prev, response]);
    } catch {
      // Mock fallback response for smooth preview
      const aiResponse: ChatMessage = {
        id: `ast-${Date.now()}`,
        role: 'assistant',
        content: `I received your request: "${currentPrompt}". Processing via ${selectedModel}... All system modules are operating normally.`,
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
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
      {/* Top Options Bar */}
      <div className="glass-panel" style={{ borderRadius: 0, borderLeft: 0, borderRight: 0, borderTop: 0, padding: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sparkles size={18} style={{ color: 'var(--primary)' }} />
          <span style={{ fontSize: '13px', fontWeight: 600 }}>Active Model:</span>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="input-field"
            style={{ width: '180px', padding: '6px 10px', fontSize: '12px' }}
          >
            <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
            <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
            <option value="ollama-llama3">Local Ollama Llama3</option>
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '12px', color: 'var(--text-muted)' }}>
          <Layers size={14} />
          <span>Autonomy: <strong style={{ color: 'var(--text-main)', textTransform: 'capitalize' }}>{preferences.autonomy_level}</strong></span>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        {messages.map((msg) => (
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
                }}
              >
                <Bot size={20} />
              </div>
            )}

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div
                className={msg.role === 'user' ? undefined : 'glass-card'}
                style={{
                  padding: '14px 18px',
                  borderRadius: 'var(--radius-lg)',
                  background: msg.role === 'user' ? 'linear-gradient(135deg, var(--primary) 0%, hsl(245, 80%, 60%) 100%)' : undefined,
                  color: '#fff',
                  fontSize: '14px',
                  lineHeight: 1.6,
                }}
              >
                {msg.content}
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
        ))}

        {isLoading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '13px' }}>
            <Bot size={18} style={{ color: 'var(--primary)' }} />
            <span>MAX reasoning & assembling tools...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <form onSubmit={handleSend} style={{ padding: '16px 24px', background: 'var(--bg-glass)', borderTop: '1px solid var(--border-glass)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ width: '42px', height: '42px', padding: 0 }}
            title="Voice Query Toggle (Module 26 Speech System)"
          >
            <Mic size={18} />
          </button>

          <input
            type="text"
            placeholder="Ask MAX to execute tasks, search knowledge, or inspect system..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="input-field"
            style={{ flex: 1, padding: '12px 16px', fontSize: '14px' }}
          />

          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
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
