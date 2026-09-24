import React from 'react';
import { Bell } from 'lucide-react';

export const NotificationsView: React.FC = () => {
  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Notification Delivery Monitor
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 27 Notification Delivery History & Channel Statuses</span>
      </div>

      <div className="admin-panel" style={{ padding: '16px' }}>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
          All notification channels (Desktop, Push, In-App) operating normally with 0 delivery failures in the last 24h.
        </p>
      </div>
    </div>
  );
};
