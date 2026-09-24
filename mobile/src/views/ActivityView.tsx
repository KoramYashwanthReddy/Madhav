import React, { useState, useEffect } from 'react';
import { AuditEvent } from '../types';
import { mobileApiClient } from '../api/client';
import { Activity } from 'lucide-react';

export const ActivityView: React.FC = () => {
  const [logs, setLogs] = useState<AuditEvent[]>([]);

  useEffect(() => {
    mobileApiClient.getActivityLogs().then(setLogs);
  }, []);

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Audit Activity
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 33 User-Safe Telemetry Audit</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {logs.map((log) => (
          <div key={log.id} className="glass-card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>{log.event_type}</span>
              <span style={{ color: 'var(--text-dim)' }}>{new Date(log.timestamp).toLocaleTimeString()}</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-main)', margin: 0 }}>{log.details}</p>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Origin: {log.module_origin}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
