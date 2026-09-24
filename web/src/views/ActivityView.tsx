import React, { useState, useEffect } from 'react';
import { AuditEvent } from '../types';
import { webApiClient } from '../api/client';
import { Activity, ShieldCheck, Terminal, AlertCircle } from 'lucide-react';

export const ActivityView: React.FC = () => {
  const [logs, setLogs] = useState<AuditEvent[]>([]);

  useEffect(() => {
    webApiClient.getActivityLogs().then(setLogs);
  }, []);

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          Observability & Audit Stream
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 33 Observability & Structured Telemetry Audit Log
        </p>
      </div>

      <div className="glass-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--border-glass)', color: 'var(--text-muted)' }}>
              <th style={{ padding: '10px' }}>Timestamp</th>
              <th style={{ padding: '10px' }}>Event Type</th>
              <th style={{ padding: '10px' }}>Module Origin</th>
              <th style={{ padding: '10px' }}>Severity</th>
              <th style={{ padding: '10px' }}>Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                <td style={{ padding: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>
                  {new Date(log.timestamp).toLocaleTimeString()}
                </td>
                <td style={{ padding: '10px', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                  {log.event_type}
                </td>
                <td style={{ padding: '10px', color: 'var(--text-muted)' }}>
                  {log.module_origin}
                </td>
                <td style={{ padding: '10px' }}>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: log.severity === 'critical' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                      color: log.severity === 'critical' ? 'hsl(350, 89%, 65%)' : 'var(--primary)',
                    }}
                  >
                    {log.severity.toUpperCase()}
                  </span>
                </td>
                <td style={{ padding: '10px', color: 'var(--text-main)' }}>
                  {log.details}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
