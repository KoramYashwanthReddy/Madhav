import React, { useState, useEffect } from 'react';
import { SystemResourceStatus } from '../types';
import { webApiClient } from '../api/client';
import { Cpu, HardDrive, Wifi, Server, Activity } from 'lucide-react';

export const SystemView: React.FC = () => {
  const [systemStatus, setSystemStatus] = useState<SystemResourceStatus | null>(null);

  useEffect(() => {
    webApiClient.getSystemStatus().then(setSystemStatus);
  }, []);

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          System Telemetry & Resource Health
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 01 Platform Foundation & Module 33 Observability Infrastructure
        </p>
      </div>

      {systemStatus && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div className="glass-card metric-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span className="metric-title">CPU Utilization</span>
                <Cpu size={18} style={{ color: 'var(--primary)' }} />
              </div>
              <div className="metric-value">{systemStatus.cpu_usage_percent}%</div>
            </div>

            <div className="glass-card metric-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span className="metric-title">Memory Allocation</span>
                <HardDrive size={18} style={{ color: 'var(--accent-purple)' }} />
              </div>
              <div className="metric-value">{systemStatus.memory_used_mb} MB</div>
              <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>Of {systemStatus.memory_total_mb} MB total</span>
            </div>

            <div className="glass-card metric-card">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span className="metric-title">Active Connections</span>
                <Wifi size={18} style={{ color: 'var(--status-online)' }} />
              </div>
              <div className="metric-value">{systemStatus.active_websocket_connections} WebSocket</div>
            </div>
          </div>

          <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginTop: '12px' }}>
            Model Provider Status & Latencies
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {systemStatus.model_providers.map((p, idx) => (
              <div key={idx} className="glass-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Server size={18} style={{ color: 'var(--accent-cyan)' }} />
                  <div>
                    <h5 style={{ fontSize: '14px', fontWeight: 600, margin: 0, color: 'var(--text-main)' }}>{p.name}</h5>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Latency: {p.latency_ms}ms</span>
                  </div>
                </div>
                <span className="status-badge">
                  <span className={`status-dot ${p.status === 'online' ? 'online' : ''}`} />
                  <span>{p.status}</span>
                </span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
};
