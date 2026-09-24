import React, { useState, useEffect } from 'react';
import { AuditEvent } from '../types';
import { adminApiClient } from '../api/admin/client';
import { redactValue } from '../utils/redactSecrets';
import { FileText, Search } from 'lucide-react';

export const AuditView: React.FC = () => {
  const [logs, setLogs] = useState<AuditEvent[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    adminApiClient.getAuditLogs(searchQuery).then(setLogs);
  }, [searchQuery]);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Audit Explorer & Traceability
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 33 Audit Engine with Automatic Secret Redaction</span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Search size={15} style={{ position: 'absolute', left: '10px', top: '9px', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search by actor, action, resource, or trace ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field"
            style={{ paddingLeft: '32px' }}
          />
        </div>
      </div>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Actor</th>
              <th>Action</th>
              <th>Resource</th>
              <th>Module Origin</th>
              <th>Trace ID</th>
              <th>Severity</th>
              <th>Details (Redacted)</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: 'var(--text-dim)' }}>
                  {new Date(l.timestamp).toLocaleTimeString()}
                </td>
                <td style={{ fontWeight: 600 }}>{l.actor}</td>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{l.action}</td>
                <td>{l.resource}</td>
                <td>{l.module_origin}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{l.trace_id}</td>
                <td>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-sm)',
                      background: l.severity === 'critical' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(99, 102, 241, 0.2)',
                      color: l.severity === 'critical' ? 'hsl(350, 89%, 65%)' : 'var(--primary)',
                    }}
                  >
                    {l.severity.toUpperCase()}
                  </span>
                </td>
                <td style={{ fontSize: '12px', color: 'var(--text-main)' }}>
                  {String(redactValue('details', l.details))}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
