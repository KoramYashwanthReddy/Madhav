import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { Bell, ShieldAlert, Check } from 'lucide-react';

export const NotificationsView: React.FC = () => {
  const { notifications, markNotificationRead } = useMobileApp();

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Mobile Alerts
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 27 Notification System & Proactive Alerts</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {notifications.map((item) => (
          <div
            key={item.id}
            className="glass-card"
            style={{
              padding: '14px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '10px',
              opacity: item.read ? 0.6 : 1,
            }}
          >
            <Bell size={18} style={{ color: 'var(--primary)', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>{item.title}</div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>{item.message}</p>
            </div>
            {!item.read && (
              <button
                onClick={() => markNotificationRead(item.id)}
                className="btn btn-secondary"
                style={{ minHeight: '30px', padding: '4px 8px', fontSize: '10px' }}
              >
                <Check size={12} />
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
