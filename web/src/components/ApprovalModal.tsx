import React from 'react';
import { useWebApp } from '../context/WebAppContext';
import { ShieldAlert, CheckCircle2, XCircle, Terminal, AlertTriangle } from 'lucide-react';

export const ApprovalModal: React.FC = () => {
  const { pendingApprovals, handleApprovalResponse } = useWebApp();

  if (!Array.isArray(pendingApprovals) || pendingApprovals.length === 0) return null;

  const current = pendingApprovals[0];

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(8px)',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: '520px',
          maxWidth: '95vw',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-lg)',
          overflow: 'hidden',
          boxShadow: '0 20px 60px rgba(239, 68, 68, 0.2)',
        }}
      >
        {/* Header */}
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', padding: '16px 20px', borderBottom: '1px solid rgba(239, 68, 68, 0.3)', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <ShieldAlert size={24} style={{ color: 'hsl(350, 89%, 60%)' }} />
          <div>
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '16px', fontWeight: 700, color: 'var(--text-main)', margin: 0 }}>
              Module 15 Security Approval Required
            </h2>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Risk Level: <strong style={{ color: 'hsl(350, 89%, 65%)', textTransform: 'uppercase' }}>{current.risk_level}</strong>
            </span>
          </div>
        </div>

        {/* Body Content */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
              Action Description
            </label>
            <p style={{ fontSize: '14px', color: 'var(--text-main)', marginTop: '4px', fontWeight: 500 }}>
              {current.description}
            </p>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
              Target Tool Name
            </label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
              <Terminal size={16} style={{ color: 'var(--primary)' }} />
              <code style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: 'var(--accent-cyan)', background: 'rgba(0,0,0,0.3)', padding: '4px 8px', borderRadius: '4px' }}>
                {current.tool_name}
              </code>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 600 }}>
              Arguments Payload
            </label>
            <pre
              style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                background: 'rgba(0,0,0,0.4)',
                padding: '12px',
                borderRadius: 'var(--radius-md)',
                color: 'var(--text-muted)',
                overflowX: 'auto',
                border: '1px solid var(--border-glass)',
                marginTop: '4px',
              }}
            >
              {JSON.stringify(current.arguments, null, 2)}
            </pre>
          </div>

          <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', borderRadius: 'var(--radius-md)', padding: '10px 14px', display: 'flex', alignItems: 'center', gap: '10px', fontSize: '12px', color: 'hsl(38, 92%, 65%)' }}>
            <AlertTriangle size={18} style={{ flexShrink: 0 }} />
            <span>Review payload details carefully before approving tool execution.</span>
          </div>
        </div>

        {/* Footer Actions */}
        <div style={{ padding: '16px 20px', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={() => handleApprovalResponse(current.id, false)}
            className="btn btn-secondary"
          >
            <XCircle size={16} />
            <span>Deny Action</span>
          </button>

          <button
            onClick={() => handleApprovalResponse(current.id, true)}
            className="btn btn-primary"
            style={{ background: 'linear-gradient(135deg, hsl(152, 69%, 45%) 0%, hsl(152, 69%, 55%) 100%)' }}
          >
            <CheckCircle2 size={16} />
            <span>Authorize Execution</span>
          </button>
        </div>
      </div>
    </div>
  );
};
