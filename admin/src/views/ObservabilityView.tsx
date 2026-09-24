import React, { useState, useEffect } from 'react';
import { TraceSpan } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Activity, BarChart2, FileText, Network } from 'lucide-react';

export const ObservabilityView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'logs' | 'metrics' | 'traces'>('traces');
  const [traces, setTraces] = useState<TraceSpan[]>([]);

  useEffect(() => {
    adminApiClient.getTraces().then(setTraces);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Observability Console
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 33 Observability Infrastructure — Logs, Metrics & Distributed Tracing</span>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '8px' }}>
        <button
          onClick={() => setActiveTab('traces')}
          className={activeTab === 'traces' ? 'btn btn-primary' : 'btn btn-secondary'}
          style={{ padding: '6px 14px' }}
        >
          <Network size={14} /> Traces Timeline
        </button>
        <button
          onClick={() => setActiveTab('metrics')}
          className={activeTab === 'metrics' ? 'btn btn-primary' : 'btn btn-secondary'}
          style={{ padding: '6px 14px' }}
        >
          <BarChart2 size={14} /> Metrics
        </button>
        <button
          onClick={() => setActiveTab('logs')}
          className={activeTab === 'logs' ? 'btn btn-primary' : 'btn btn-secondary'}
          style={{ padding: '6px 14px' }}
        >
          <FileText size={14} /> Log Stream
        </button>
      </div>

      {activeTab === 'traces' && (
        <div className="admin-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 600, margin: 0 }}>Distributed Execution Trace Spans</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {traces.map((sp) => (
              <div key={sp.id} className="admin-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>{sp.component} ➔ {sp.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>Trace ID: {sp.trace_id}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className="admin-status-badge">
                    <span className="status-dot healthy" />
                    <span>{sp.duration_ms}ms</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'metrics' && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
          <div className="admin-card">
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Throughput</span>
            <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '4px 0 0 0' }}>42 req/sec</h3>
          </div>
          <div className="admin-card">
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Error Rate</span>
            <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '4px 0 0 0', color: 'var(--status-healthy)' }}>0.01%</h3>
          </div>
        </div>
      )}

      {activeTab === 'logs' && (
        <div className="admin-panel" style={{ padding: '16px', fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--text-muted)' }}>
          <div>[INFO] [Module 01 Platform] Health check passed on 127.0.0.1:8000</div>
          <div>[INFO] [Module 15 Security] Granted authorization for read_file execution</div>
          <div>[INFO] [Module 33 Audit] Emitted safe audit log trace tr-8813</div>
        </div>
      )}
    </div>
  );
};
