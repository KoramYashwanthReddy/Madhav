import React, { useState } from 'react';
import { useAdmin } from '../context/AdminContext';
import { AlertTriangle, CheckCircle2, XCircle } from 'lucide-react';

export const DangerousActionModal: React.FC = () => {
  const { dangerousActionModal, closeDangerousActionModal } = useAdmin();
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!dangerousActionModal || !dangerousActionModal.isOpen) return null;

  const handleConfirm = async () => {
    setIsSubmitting(true);
    try {
      await dangerousActionModal.onConfirm();
    } finally {
      setIsSubmitting(false);
      closeDangerousActionModal();
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(6px)',
        zIndex: 10000,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      }}
    >
      <div
        className="admin-panel"
        style={{
          width: '500px',
          maxWidth: '95vw',
          border: '1px solid rgba(245, 158, 11, 0.5)',
          borderRadius: 'var(--radius-md)',
        }}
      >
        <div style={{ background: 'rgba(245, 158, 11, 0.15)', padding: '14px 18px', borderBottom: '1px solid rgba(245, 158, 11, 0.3)', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertTriangle size={20} style={{ color: 'hsl(38, 92%, 60%)' }} />
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>
            {dangerousActionModal.title}
          </h3>
        </div>

        <div style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <p style={{ fontSize: '13px', color: 'var(--text-main)', margin: 0, lineHeight: 1.5 }}>
            {dangerousActionModal.description}
          </p>

          <div style={{ fontSize: '11px', color: 'var(--text-dim)', background: 'rgba(0,0,0,0.3)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)' }}>
            Target ID: {dangerousActionModal.targetId} • Action: {dangerousActionModal.actionType}
          </div>
        </div>

        <div style={{ padding: '12px 18px', background: 'rgba(0,0,0,0.3)', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
          <button onClick={closeDangerousActionModal} className="btn btn-secondary">
            <XCircle size={15} />
            <span>Cancel</span>
          </button>

          <button onClick={handleConfirm} disabled={isSubmitting} className="btn btn-primary" style={{ background: 'hsl(38, 92%, 50%)' }}>
            <CheckCircle2 size={15} />
            <span>{isSubmitting ? 'Executing...' : 'Authorize Action'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
