import React from 'react';
import { useAdmin } from '../context/AdminContext';
import { Search, Bell, ShieldAlert, AlertOctagon, UserCheck, Shield } from 'lucide-react';

export const AdminHeader: React.FC = () => {
  const {
    securityMode,
    adminRole,
    alerts,
    setIsGlobalSearchOpen,
    setIsKillSwitchModalOpen,
    isReadOnly,
  } = useAdmin();

  return (
    <header
      className="admin-panel"
      style={{
        height: '60px',
        borderRadius: 0,
        borderTop: 0,
        borderLeft: 0,
        borderRight: 0,
        padding: '0 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        zIndex: 10,
      }}
    >
      {/* Brand & Console Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: 'linear-gradient(135deg, hsl(350, 89%, 55%) 0%, var(--primary) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800 }}>
            M
          </div>
          <div>
            <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '16px', fontWeight: 700, margin: 0, lineHeight: 1.2, letterSpacing: '0.5px' }}>
              MAX SYSTEM CONSOLE
            </h1>
            <span style={{ fontSize: '10px', color: 'var(--text-muted)', display: 'block' }}>
              Enterprise Operational Administration
            </span>
          </div>
        </div>

        {/* Security Mode Pill */}
        <div className="admin-status-badge">
          <span className={`status-dot ${securityMode === 'NORMAL' ? 'healthy' : 'danger'}`} />
          <span>SECURITY MODE: {securityMode}</span>
        </div>

        {isReadOnly && (
          <span className="admin-status-badge" style={{ background: 'rgba(234, 179, 8, 0.2)', color: 'hsl(38, 92%, 60%)' }}>
            READ ONLY MODE
          </span>
        )}
      </div>

      {/* Global Admin Search Bar */}
      <button
        onClick={() => setIsGlobalSearchOpen(true)}
        className="admin-card"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '6px 14px',
          width: '320px',
          color: 'var(--text-muted)',
          cursor: 'pointer',
        }}
        aria-label="Global Admin Search (Control K)"
      >
        <Search size={15} />
        <span style={{ fontSize: '12px', flex: 1, textAlign: 'left' }}>Search audit, tasks, tools, devices...</span>
        <kbd style={{ fontSize: '10px', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '3px' }}>
          Ctrl K
        </kbd>
      </button>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Emergency Kill Switch Button */}
        <button
          onClick={() => setIsKillSwitchModalOpen(true)}
          className="btn btn-danger"
          style={{ padding: '6px 12px', fontSize: '11px' }}
          aria-label="Emergency System Kill Switch"
        >
          <AlertOctagon size={15} />
          <span>EMERGENCY KILL SWITCH</span>
        </button>

        {/* Role Pill */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.3)', padding: '4px 10px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-color)' }}>
          <UserCheck size={14} style={{ color: 'var(--primary)' }} />
          <span>{adminRole}</span>
        </div>
      </div>
    </header>
  );
};
