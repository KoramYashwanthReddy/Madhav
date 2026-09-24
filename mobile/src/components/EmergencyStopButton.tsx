import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { AlertOctagon, RefreshCw } from 'lucide-react';

export const EmergencyStopButton: React.FC = () => {
  const { isEmergencyStopped, resetEmergencyStop, triggerEmergencyStop } = useMobileApp();

  if (!isEmergencyStopped) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: '64px',
        left: '16px',
        right: '16px',
        background: 'rgba(239, 68, 68, 0.95)',
        backdropFilter: 'blur(10px)',
        borderRadius: 'var(--radius-md)',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 800,
        boxShadow: '0 8px 24px rgba(239, 68, 68, 0.4)',
        color: '#fff',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <AlertOctagon size={20} />
        <div>
          <strong style={{ fontSize: '13px', display: 'block' }}>Emergency Stop Active</strong>
          <span style={{ fontSize: '11px', opacity: 0.9 }}>All mobile agent operations halted.</span>
        </div>
      </div>

      <button
        onClick={resetEmergencyStop}
        style={{
          background: 'rgba(255, 255, 255, 0.2)',
          border: 'none',
          color: '#fff',
          padding: '6px 12px',
          borderRadius: 'var(--radius-sm)',
          fontSize: '12px',
          fontWeight: 700,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
        }}
      >
        <RefreshCw size={14} />
        <span>Reset</span>
      </button>
    </div>
  );
};
