import React, { useState, useEffect } from 'react';
import { AgentInfo } from '../types';
import { webApiClient } from '../api/client';
import { Bot, Cpu, Shield, CheckCircle2 } from 'lucide-react';

export const AgentsView: React.FC = () => {
  const [agents, setAgents] = useState<AgentInfo[]>([]);

  useEffect(() => {
    webApiClient.getAgents().then(setAgents);
  }, []);

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          Autonomous Agents Registry
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Modules 16–26 (Computer, Filesystem, Terminal, Browser, Coding, GitHub, Vision, Speech)
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        {agents.map((ag) => (
          <div key={ag.id} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ width: '36px', height: '36px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
                  <Bot size={20} />
                </div>
                <div>
                  <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{ag.name}</h4>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module {ag.module_number} — {ag.role}</span>
                </div>
              </div>

              <span className="status-badge">
                <span className={`status-dot ${ag.status === 'active' ? 'online' : ''}`} />
                <span>{ag.status}</span>
              </span>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{ag.description}</p>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {ag.capabilities.map((cap, idx) => (
                <span key={idx} style={{ fontSize: '11px', background: 'rgba(255,255,255,0.06)', padding: '2px 8px', borderRadius: '4px', fontFamily: 'var(--font-mono)' }}>
                  {cap}
                </span>
              ))}
            </div>

            <div style={{ fontSize: '11px', color: 'var(--text-dim)', borderTop: '1px solid var(--border-glass)', paddingTop: '8px' }}>
              Tasks Completed: <strong>{ag.tasks_completed}</strong>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
