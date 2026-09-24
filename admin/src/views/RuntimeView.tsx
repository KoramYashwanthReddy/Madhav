import React, { useState, useEffect } from 'react';
import { AIRuntimeStatus } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Cpu, Server, Activity } from 'lucide-react';

export const RuntimeView: React.FC = () => {
  const [runtime, setRuntime] = useState<AIRuntimeStatus | null>(null);

  useEffect(() => {
    adminApiClient.getAIRuntime().then(setRuntime);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          AI Runtime Telemetry
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 04 AI Runtime & LLM Inference Manager</span>
      </div>

      {runtime && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
            <div className="admin-card">
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Active Provider</span>
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: '4px 0 0 0', color: 'var(--accent-cyan)' }}>{runtime.provider}</h3>
            </div>
            <div className="admin-card">
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Requests Handled</span>
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: '4px 0 0 0', color: 'var(--text-main)' }}>{runtime.request_count}</h3>
            </div>
            <div className="admin-card">
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Tokens Processed</span>
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: '4px 0 0 0', color: 'var(--primary)' }}>{runtime.tokens_processed.toLocaleString()}</h3>
            </div>
            <div className="admin-card">
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Average Latency</span>
              <h3 style={{ fontSize: '16px', fontWeight: 700, margin: '4px 0 0 0', color: 'var(--status-healthy)' }}>{runtime.latency_ms}ms</h3>
            </div>
          </div>

          <div className="admin-panel" style={{ padding: '16px', marginTop: '8px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, margin: '0 0 10px 0' }}>Runtime Capability Flag Matrix</h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {runtime.capabilities.map((cap, idx) => (
                <span key={idx} style={{ fontSize: '11px', background: 'rgba(255,255,255,0.06)', padding: '4px 8px', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)' }}>
                  {cap}
                </span>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
