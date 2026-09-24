import React from 'react';
import { useWebApp } from '../context/WebAppContext';
import { Bell, Check, ShieldAlert, Info, AlertTriangle } from 'lucide-react';

export const NotificationsView: React.FC = () => {
  const { notifications, markNotificationRead } = useWebApp();

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          Proactive Notifications & Alerts
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 27 Notification System & Module 30 Proactive Intelligence
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {notifications.map((item) => (
          <div
            key={item.id}
            className="glass-card"
            style={{
              padding: '18px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '14px',
              opacity: item.read ? 0.6 : 1,
            }}
          >
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary)' }}>
              {item.category === 'approval' ? <ShieldAlert size={18} style={{ color: 'var(--status-danger)' }} /> : <Bell size={18} />}
            </div>

            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{item.title}</h4>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                  {new Date(item.timestamp).toLocaleString()}
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px', margin: 0 }}>
                {item.message}
              </p>
            </div>

            {!item.read && (
              <button
                onClick={() => markNotificationRead(item.id)}
                className="btn btn-secondary"
                style={{ padding: '6px 10px', fontSize: '11px' }}
              >
                <Check size={12} />
                <span>Mark Read</span>
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
