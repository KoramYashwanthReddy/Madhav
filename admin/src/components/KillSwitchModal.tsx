import React, { useState } from 'react';
import { useAdmin } from '../context/AdminContext';
import { AlertOctagon, ShieldAlert, XCircle, CheckCircle2 } from 'lucide-react';

export const KillSwitchModal: React.FC = () => {
  const { isKillSwitchModalOpen, setIsKillSwitchModalOpen, triggerKillSwitch } = useAdmin();
  const [confirmInput, setConfirmInput] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isKillSwitchModalOpen) return null;

  const handleConfirm = async () => {
    if (confirmInput.trim().toUpperCase() !== 'LOCKDOWN') return;
    setIsSubmitting(true);
    try {
      await triggerKillSwitch();
    } finally {
      setIsSubmitting(false);
      setConfirmInput('');
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.85)',
        backdropFilter: 'blur(8px)',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
      onClick={() => setIsKillSwitchModalOpen(false)}
    >
      <div
        className="admin-panel"
        style={{
          width: '540px',
          maxWidth: '95vw',
          border: '2px solid var(--status-danger)',
          borderRadius: 'var(--radius-md)',
          boxShadow: '0 20px 60px rgba(239, 68, 68, 0.4)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ background: 'rgba(239, 68, 68, 0.2)', padding: '16px 20px', borderBottom: '1px solid rgba(239, 68, 68, 0.4)', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertOctagon size={24} style={{ color: 'hsl(350, 89%, 60%)' }} />
          <div>
            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '16px', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
              EMERGENCY SYSTEM KILL SWITCH
            </h3>
            <span style={{ fontSize: '11px', color: 'hsl(350, 89%, 70%)', fontWeight: 600 }}>
              Module 15 Security Engine High-Privilege Action
            </span>
          </div>
        </div>

        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '12px', borderRadius: 'var(--radius-sm)', fontSize: '13px', color: 'var(--text-main)', lineHeight: 1.5 }}>
            <strong>WARNING & CONSEQUENCES:</strong>
            <ul style={{ paddingLeft: '18px', marginTop: '6px' }}>
              <li>Transitions System Security Mode to <strong>LOCKDOWN</strong>.</li>
              <li>Halts all active autonomous multi-agent task execution.</li>
              <li>Revokes temporary tool execution permissions across Desktop, Web, and Mobile.</li>
              <li>Emits an emergency audit event to Module 33 Observability.</li>
            </ul>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase' }}>
              To confirm kill switch trigger, type "LOCKDOWN" below:
            </label>
            <input
              type="text"
              value={confirmInput}
              onChange={(e) => setConfirmInput(e.target.value)}
              placeholder="Type LOCKDOWN"
              className="input-field"
              style={{ marginTop: '6px', fontFamily: 'var(--font-mono)' }}
            />
          </div>
        </div>

        <div style={{ padding: '14px 20px', background: 'rgba(0,0,0,0.3)', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button
            onClick={() => setIsKillSwitchModalOpen(false)}
            className="btn btn-secondary"
          >
            <XCircle size={15} />
            <span>Cancel</span>
          </button>

          <button
            onClick={handleConfirm}
            disabled={confirmInput.trim().toUpperCase() !== 'LOCKDOWN' || isSubmitting}
            className="btn btn-danger"
          >
            <CheckCircle2 size={15} />
            <span>{isSubmitting ? 'Activating Lockdown...' : 'CONFIRM KILL SWITCH'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
