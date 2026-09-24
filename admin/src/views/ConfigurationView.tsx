import React, { useState, useEffect } from 'react';
import { ConfigSetting } from '../types';
import { adminApiClient } from '../api/admin/client';
import { redactValue } from '../utils/redactSecrets';
import { Sliders, Lock } from 'lucide-react';

export const ConfigurationView: React.FC = () => {
  const [configs, setConfigs] = useState<ConfigSetting[]>([]);

  useEffect(() => {
    adminApiClient.getConfiguration().then(setConfigs);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Safe System Configuration Viewer
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 02 Environment & Operational Settings (Secrets Redacted)</span>
      </div>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Setting Key</th>
              <th>Environment</th>
              <th>Effective Value (Redacted)</th>
              <th>Source</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {configs.map((c, idx) => (
              <tr key={idx}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{c.name}</td>
                <td>{c.environment}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>
                  {c.is_secret ? (
                    <span style={{ color: 'hsl(38, 92%, 60%)', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <Lock size={12} /> [REDACTED_SECRET]
                    </span>
                  ) : (
                    String(redactValue(c.name, c.value))
                  )}
                </td>
                <td style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{c.effective_source}</td>
                <td>
                  <span className="admin-status-badge">
                    <span className="status-dot healthy" />
                    <span>{c.status.toUpperCase()}</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
