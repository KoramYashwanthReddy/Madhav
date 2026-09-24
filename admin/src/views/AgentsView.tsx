import React, { useState, useEffect } from 'react';
import { AgentInfo } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Bot, Play, Pause, RefreshCw } from 'lucide-react';

export const AgentsView: React.FC = () => {
  const [agents, setAgents] = useState<AgentInfo[]>([]);

  useEffect(() => {
    adminApiClient.getAgents().then(setAgents);
  }, []);

  const handleControl = async (id: string, action: 'pause' | 'resume' | 'restart') => {
    await adminApiClient.controlAgent(id, action);
    const updated = await adminApiClient.getAgents();
    setAgents(updated);
  };

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Agent Engine Monitor
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 13 Agent Delegation & Operational Controls</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '12px' }}>
        {agents.map((ag) => (
          <div key={ag.id} className="admin-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Bot size={18} style={{ color: 'var(--primary)' }} />
                <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{ag.name}</h4>
              </div>
              <span className="admin-status-badge">
                <span className={`status-dot ${ag.status === 'running' ? 'healthy' : ''}`} />
                <span>{ag.status.toUpperCase()}</span>
              </span>
            </div>

            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module {ag.module_number} — {ag.role}</span>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
              {ag.capabilities.map((c, idx) => (
                <span key={idx} style={{ fontSize: '10px', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)' }}>
                  {c}
                </span>
              ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)', paddingTop: '10px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Completed Tasks: {ag.tasks_completed}</span>

              <div style={{ display: 'flex', gap: '6px' }}>
                {ag.status === 'running' ? (
                  <button onClick={() => handleControl(ag.id, 'pause')} className="btn btn-secondary" style={{ padding: '3px 8px', fontSize: '10px' }}>
                    <Pause size={12} /> Pause
                  </button>
                ) : (
                  <button onClick={() => handleControl(ag.id, 'resume')} className="btn btn-primary" style={{ padding: '3px 8px', fontSize: '10px' }}>
                    <Play size={12} /> Resume
                  </button>
                )}
                <button onClick={() => handleControl(ag.id, 'restart')} className="btn btn-secondary" style={{ padding: '3px 8px', fontSize: '10px' }}>
                  <RefreshCw size={12} /> Restart
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
