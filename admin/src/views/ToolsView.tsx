import React, { useState, useEffect } from 'react';
import { ToolDefinition } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Wrench, ShieldAlert, CheckCircle2 } from 'lucide-react';

export const ToolsView: React.FC = () => {
  const [tools, setTools] = useState<ToolDefinition[]>([]);

  useEffect(() => {
    adminApiClient.getTools().then(setTools);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Tool Registry & Risk Schema
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 14 Tool Registry & Module 15 Approval Flags</span>
      </div>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Tool Name</th>
              <th>Category</th>
              <th>Version</th>
              <th>Risk Level</th>
              <th>Approval Requirement</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {tools.map((t, idx) => (
              <tr key={idx}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--accent-cyan)' }}>{t.name}</td>
                <td>{t.category}</td>
                <td>{t.version}</td>
                <td>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-sm)',
                      background: t.risk_level === 'high' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(255,255,255,0.06)',
                      color: t.risk_level === 'high' ? 'hsl(350, 89%, 65%)' : 'var(--text-main)',
                      textTransform: 'uppercase',
                    }}
                  >
                    {t.risk_level}
                  </span>
                </td>
                <td>
                  {t.requires_approval ? (
                    <span style={{ color: 'hsl(350, 89%, 65%)', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <ShieldAlert size={12} /> Approval Required
                    </span>
                  ) : (
                    <span style={{ color: 'var(--status-healthy)', fontWeight: 600 }}>Auto Approved</span>
                  )}
                </td>
                <td>
                  <span className="admin-status-badge">
                    <span className={`status-dot ${t.enabled ? 'healthy' : 'danger'}`} />
                    <span>{t.enabled ? 'ENABLED' : 'DISABLED'}</span>
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
