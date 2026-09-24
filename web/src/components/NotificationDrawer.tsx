import React from 'react';
import { useWebApp } from '../context/WebAppContext';
import { X, Bell, ShieldAlert, Info, AlertTriangle, CheckCircle } from 'lucide-react';

export const NotificationDrawer: React.FC = () => {
  const {
    isNotificationDrawerOpen,
    setIsNotificationDrawerOpen,
    notifications,
    markNotificationRead,
    pendingApprovals,
  } = useWebApp();

  if (!isNotificationDrawerOpen) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0,0,0,0.5)',
        backdropFilter: 'blur(4px)',
        zIndex: 9000,
        display: 'flex',
        justifyContent: 'flex-end',
      }}
      onClick={() => setIsNotificationDrawerOpen(false)}
    >
      <div
        className="glass-panel"
        style={{
          width: '400px',
          maxWidth: '100vw',
          height: '100vh',
          borderRadius: 0,
          borderRight: 0,
          borderTop: 0,
          borderBottom: 0,
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '-10px 0 30px rgba(0,0,0,0.5)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ padding: '20px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Bell size={20} style={{ color: 'var(--primary)' }} />
            <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '16px', fontWeight: 700, margin: 0 }}>
              Notifications & Alerts
            </h2>
          </div>
          <button
            onClick={() => setIsNotificationDrawerOpen(false)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* List Content */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Pending Security Approvals Section */}
          {Array.isArray(pendingApprovals) && pendingApprovals.length > 0 && (
            <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-md)', padding: '14px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'hsl(350, 89%, 65%)', fontWeight: 600, fontSize: '13px', marginBottom: '6px' }}>
                <ShieldAlert size={16} />
                <span>Security Approval Requested</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
                {pendingApprovals[0].description}
              </p>
            </div>
          )}

          {!Array.isArray(notifications) || notifications.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'var(--text-muted)', fontSize: '13px' }}>
              No recent notifications or proactive intelligence alerts.
            </div>
          ) : (
            notifications.map((item) => (
              <div
                key={item.id}
                onClick={() => markNotificationRead(item.id)}
                className="glass-card"
                style={{
                  padding: '14px',
                  borderRadius: 'var(--radius-md)',
                  opacity: item.read ? 0.65 : 1,
                  borderLeft: `4px solid ${
                    item.category === 'approval'
                      ? 'var(--status-danger)'
                      : item.category === 'alert'
                      ? 'var(--status-warning)'
                      : 'var(--primary)'
                  }`,
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>{item.title}</span>
                  <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
                    {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                  {item.message}
                </p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
