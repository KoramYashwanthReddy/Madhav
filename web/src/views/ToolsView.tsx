import React, { useState, useEffect } from 'react';
import { ToolDefinition } from '../types';
import { webApiClient } from '../api/client';
import { Wrench, ShieldAlert, CheckCircle, Terminal } from 'lucide-react';

export const ToolsView: React.FC = () => {
  const [tools, setTools] = useState<ToolDefinition[]>([]);

  useEffect(() => {
    webApiClient.getTools().then(setTools);
  }, []);

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          Tool Registry & Capability Sandbox
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 14 Tool Registry & Module 15 Permission Authorization
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {tools.map((tool, idx) => (
          <div key={idx} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Wrench size={18} style={{ color: 'var(--primary)' }} />
                <code style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                  {tool.name}
                </code>
              </div>

              {tool.requires_approval ? (
                <span style={{ fontSize: '10px', background: 'rgba(239, 68, 68, 0.2)', color: 'hsl(350, 89%, 65%)', padding: '2px 8px', borderRadius: '4px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <ShieldAlert size={12} /> Approval Required
                </span>
              ) : (
                <span style={{ fontSize: '10px', background: 'rgba(34, 197, 94, 0.2)', color: 'var(--status-online)', padding: '2px 8px', borderRadius: '4px', fontWeight: 600 }}>
                  Auto Approved
                </span>
              )}
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{tool.description}</p>

            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '10px' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontWeight: 600, textTransform: 'uppercase' }}>Parameters</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                {tool.parameters.map((p, pIdx) => (
                  <div key={pIdx} style={{ fontSize: '11px', display: 'flex', justifyContent: 'space-between', fontFamily: 'var(--font-mono)' }}>
                    <span style={{ color: 'var(--text-main)' }}>{p.name} ({p.type})</span>
                    <span style={{ color: 'var(--text-dim)' }}>{p.required ? 'Required' : 'Optional'}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
