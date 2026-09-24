import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { ShieldAlert, CheckCircle2, XCircle, Terminal } from 'lucide-react';

export const ApprovalModal: React.FC = () => {
  const { pendingApprovals, handleApprovalResponse } = useMobileApp();

  if (pendingApprovals.length === 0) return null;

  const current = pendingApprovals[0];

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 1000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '100%',
          maxWidth: '400px',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: '0 20px 50px rgba(239, 68, 68, 0.25)',
        }}
      >
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '14px 16px', borderBottom: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldAlert size={20} style={{ color: 'hsl(350, 89%, 60%)' }} />
          <div>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '15px', fontWeight: 700, margin: 0 }}>
              Module 15 Security Approval
            </h3>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
              Risk: <strong style={{ color: 'hsl(350, 89%, 65%)', textTransform: 'uppercase' }}>{current.risk_level}</strong>
            </span>
          </div>
        </div>

        <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-main)', margin: 0, fontWeight: 500 }}>
            {current.description}
          </p>

          <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal size={14} style={{ color: 'var(--primary)' }} />
            <code style={{ fontFamily: 'var(--font-mono)', fontSize: '12px', color: 'var(--accent-cyan)' }}>
              {current.tool_name}
            </code>
          </div>

          <pre
            style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              background: 'rgba(0,0,0,0.4)',
              padding: '10px',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-muted)',
              overflowX: 'auto',
              maxHeight: '120px',
            }}
          >
            {JSON.stringify(current.arguments, null, 2)}
          </pre>
        </div>

        <div style={{ padding: '12px 16px', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--border-glass)', display: 'flex', gap: '10px' }}>
          <button
            onClick={() => handleApprovalResponse(current.id, false)}
            className="btn btn-secondary"
            style={{ flex: 1 }}
          >
            <XCircle size={16} />
            <span>Deny</span>
          </button>

          <button
            onClick={() => handleApprovalResponse(current.id, true)}
            className="btn btn-primary"
            style={{ flex: 1, background: 'linear-gradient(135deg, hsl(152, 69%, 45%) 0%, hsl(152, 69%, 55%) 100%)' }}
          >
            <CheckCircle2 size={16} />
            <span>Authorize</span>
          </button>
        </div>
      </div>
    </div>
  );
};
