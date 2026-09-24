import React from 'react';
import { useWebApp } from '../context/WebAppContext';
import { Search, Bell, ShieldAlert, Sun, Moon } from 'lucide-react';

export const Header: React.FC = () => {
  const {
    health,
    pendingApprovals,
    unreadCount,
    setIsCommandPaletteOpen,
    setIsNotificationDrawerOpen,
    preferences,
    updatePreferences,
  } = useWebApp();

  const toggleTheme = () => {
    if (preferences.theme === 'glass') {
      updatePreferences({ theme: 'high-contrast' });
    } else {
      updatePreferences({ theme: 'glass' });
    }
  };

  return (
    <header className="glass-panel" style={{ height: '64px', borderRadius: 0, borderTop: 0, borderLeft: 0, borderRight: 0, padding: '0 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', zIndex: 10 }}>
      {/* Brand & System Indicator */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--primary) 0%, var(--accent-purple) 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800 }}>
            M
          </div>
          <div>
            <h1 className="gradient-text" style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0, lineHeight: 1.2 }}>
              MAX
            </h1>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>
              Personal AI Operating Layer
            </span>
          </div>
        </div>

        {/* Backend Health Status Pill */}
        <div className="status-badge" aria-label="Backend status">
          <span className={`status-dot ${health?.status === 'ok' ? 'online' : 'danger'}`} />
          <span>{health?.status === 'ok' ? `API Online (${health.active_modules} Modules)` : 'Connecting...'}</span>
        </div>
      </div>

      {/* Center Search / Command Trigger */}
      <button
        onClick={() => setIsCommandPaletteOpen(true)}
        className="glass-card"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '8px 16px',
          width: '320px',
          color: 'var(--text-muted)',
          cursor: 'pointer',
          border: '1px solid var(--border-glass)',
        }}
        aria-label="Open Command Palette (Control K)"
      >
        <Search size={16} />
        <span style={{ fontSize: '13px', flex: 1, textAlign: 'left' }}>Search knowledge, tools or ask...</span>
        <kbd style={{ fontSize: '11px', background: 'rgba(255,255,255,0.1)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-glass)' }}>
          Ctrl K
        </kbd>
      </button>

      {/* Right Action Icons */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {/* Security Approvals Pill */}
        {pendingApprovals.length > 0 && (
          <button
            onClick={() => setIsNotificationDrawerOpen(true)}
            className="btn btn-danger"
            style={{ padding: '6px 12px', fontSize: '12px' }}
            aria-label={`${pendingApprovals.length} Security Approvals Required`}
          >
            <ShieldAlert size={15} />
            <span>{pendingApprovals.length} Action Needed</span>
          </button>
        )}

        {/* High Contrast / Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="btn btn-secondary"
          style={{ width: '38px', height: '38px', padding: 0 }}
          title="Toggle High Contrast Theme"
          aria-label="Toggle Theme"
        >
          {preferences.theme === 'high-contrast' ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        {/* Notification Bell */}
        <button
          onClick={() => setIsNotificationDrawerOpen(true)}
          className="btn btn-secondary"
          style={{ width: '38px', height: '38px', padding: 0, position: 'relative' }}
          aria-label={`Notifications (${unreadCount} unread)`}
        >
          <Bell size={18} />
          {unreadCount > 0 && (
            <span
              style={{
                position: 'absolute',
                top: '4px',
                right: '4px',
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                background: 'var(--status-danger)',
                color: '#fff',
                fontSize: '10px',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {unreadCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
};
