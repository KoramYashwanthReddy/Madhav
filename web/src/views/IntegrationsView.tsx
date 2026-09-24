import React, { useState, useEffect } from 'react';
import { IntegrationConnector } from '../types';
import { webApiClient } from '../api/client';
import { Link2, CheckCircle2, XCircle } from 'lucide-react';

export const IntegrationsView: React.FC = () => {
  const [integrations, setIntegrations] = useState<IntegrationConnector[]>([]);

  useEffect(() => {
    webApiClient.getIntegrations().then(setIntegrations);
  }, []);

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          External Service Integrations
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 29 External Integrations Engine
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        {integrations.map((item) => (
          <div key={item.id} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Link2 size={18} style={{ color: 'var(--primary)' }} />
                <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{item.name}</h4>
              </div>

              {item.connected ? (
                <span className="status-badge" style={{ background: 'rgba(34, 197, 94, 0.2)', color: 'var(--status-online)' }}>
                  <CheckCircle2 size={12} /> Connected
                </span>
              ) : (
                <span className="status-badge" style={{ background: 'rgba(239, 68, 68, 0.2)', color: 'hsl(350, 89%, 65%)' }}>
                  <XCircle size={12} /> Disconnected
                </span>
              )}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)' }}>
              <span>Category: <strong style={{ color: 'var(--text-main)' }}>{item.category}</strong></span>
              <span>Status: {item.auth_status}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
