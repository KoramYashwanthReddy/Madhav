import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { ShieldAlert, BatteryCharging, Wifi, AlertOctagon, Lock } from 'lucide-react';

export const MobileHeader: React.FC = () => {
  const {
    connectionMode,
    deviceInfo,
    pendingApprovals,
    triggerEmergencyStop,
    isEmergencyStopped,
    resetEmergencyStop,
    setIsMoreDrawerOpen,
  } = useMobileApp();

  return (
    <header
      className="glass-panel"
      style={{
        height: '56px',
        padding: '0 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderLeft: 0,
        borderRight: 0,
        borderTop: 0,
        zIndex: 50,
      }}
    >
      {/* Brand & Connection Mode */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div
          style={{
            width: '28px',
            height: '28px',
            borderRadius: '6px',
            background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent-purple) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 800,
            fontSize: '13px',
            color: '#fff',
          }}
        >
          M
        </div>

        <div>
          <h1 className="gradient-text" style={{ fontFamily: 'var(--font-heading)', fontSize: '15px', fontWeight: 700, margin: 0, lineHeight: 1.1 }}>
            MAX
          </h1>
          <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
            {connectionMode} MODE
          </span>
        </div>
      </div>

      {/* Center Battery & Network Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '11px', color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <BatteryCharging size={14} style={{ color: 'var(--status-online)' }} />
          <span>{deviceInfo ? `${Math.round(deviceInfo.battery_level * 100)}%` : '88%'}</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Wifi size={14} style={{ color: connectionMode === 'OFFLINE' ? 'var(--status-danger)' : 'var(--accent-cyan)' }} />
        </div>
      </div>

      {/* Actions (Emergency Stop & Approvals) */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {pendingApprovals.length > 0 && (
          <button
            onClick={() => setIsMoreDrawerOpen(true)}
            style={{
              background: 'rgba(239, 68, 68, 0.2)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              color: 'hsl(350, 89%, 65%)',
              padding: '4px 8px',
              borderRadius: '999px',
              fontSize: '11px',
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              cursor: 'pointer',
            }}
          >
            <ShieldAlert size={12} />
            <span>{pendingApprovals.length}</span>
          </button>
        )}

        <button
          onClick={isEmergencyStopped ? resetEmergencyStop : triggerEmergencyStop}
          style={{
            background: isEmergencyStopped ? 'var(--status-danger)' : 'rgba(239, 68, 68, 0.15)',
            border: '1px solid rgba(239, 68, 68, 0.4)',
            color: isEmergencyStopped ? '#fff' : 'hsl(350, 89%, 65%)',
            padding: '6px',
            borderRadius: 'var(--radius-sm)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
          title={isEmergencyStopped ? 'Reset Emergency Stop' : 'Trigger Emergency Stop'}
          aria-label="Emergency Stop"
        >
          <AlertOctagon size={16} />
        </button>
      </div>
    </header>
  );
};
