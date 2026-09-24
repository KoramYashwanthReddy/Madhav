import React, { useState, useEffect } from 'react';
import { useAdmin } from '../context/AdminContext';
import { SecurityPolicy, SecurityViolationEvent } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Shield, AlertOctagon, ShieldAlert, CheckCircle2 } from 'lucide-react';

export const SecurityView: React.FC = () => {
  const { securityMode, setSecurityMode, setIsKillSwitchModalOpen } = useAdmin();
  const [policies, setPolicies] = useState<SecurityPolicy[]>([]);
  const [violations, setViolations] = useState<SecurityViolationEvent[]>([]);

  useEffect(() => {
    adminApiClient.getSecurityPolicies().then(setPolicies);
    adminApiClient.getSecurityViolations().then(setViolations);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Permission & Security Engine Console
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 15 Security Engine, Policy Enforcement & Emergency Kill Switch</span>
      </div>

      {/* Security Mode Banner */}
      <div className="admin-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Shield size={24} style={{ color: securityMode === 'NORMAL' ? 'var(--status-healthy)' : 'var(--status-danger)' }} />
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, margin: 0 }}>System Security Mode: {securityMode}</h3>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 15 Authoritative Permission Boundary</span>
          </div>
        </div>

        <button
          onClick={() => setIsKillSwitchModalOpen(true)}
          className="btn btn-danger"
          style={{ padding: '8px 14px' }}
        >
          <AlertOctagon size={16} />
          <span>TRIGGER KILL SWITCH</span>
        </button>
      </div>

      {/* Security Policies Table */}
      <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: '8px 0 0 0' }}>
        Active Security Enforcement Policies
      </h3>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Policy ID</th>
              <th>Version</th>
              <th>Scope</th>
              <th>Action</th>
              <th>Decision</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {policies.map((p) => (
              <tr key={p.policy_id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{p.policy_id}</td>
                <td>{p.version}</td>
                <td>{p.scope}</td>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{p.action}</td>
                <td>
                  <span
                    style={{
                      fontSize: '10px',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: 'var(--radius-sm)',
                      background: p.decision === 'ALLOW' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
                      color: p.decision === 'ALLOW' ? 'var(--status-healthy)' : 'hsl(350, 89%, 65%)',
                    }}
                  >
                    {p.decision}
                  </span>
                </td>
                <td>
                  <span className="admin-status-badge">
                    <span className="status-dot healthy" />
                    <span>ACTIVE</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recent Security Violations */}
      <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: '8px 0 0 0' }}>
        Recent Security Violations & Interceptions
      </h3>

      <div className="admin-panel" style={{ padding: '16px' }}>
        {violations.map((v) => (
          <div key={v.id} className="admin-card" style={{ display: 'flex', flexDirection: 'column', gap: '6px', borderLeft: '3px solid var(--status-danger)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px' }}>
              <span style={{ color: 'hsl(350, 89%, 65%)', fontWeight: 700 }}>VIOLATION DETECTED</span>
              <span style={{ color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>{new Date(v.timestamp).toLocaleString()}</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-main)', margin: 0 }}>{v.reason}</p>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
              Subject: {v.subject} • Resource: {v.resource} • Trace ID: {v.trace_id}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
