import React, { useState, useEffect } from 'react';
import { IntegrationConnector } from '../types';
import { mobileApiClient } from '../api/client';
import { Link2, CheckCircle2 } from 'lucide-react';

export const IntegrationsView: React.FC = () => {
  const [integrations, setIntegrations] = useState<IntegrationConnector[]>([]);

  useEffect(() => {
    mobileApiClient.getIntegrations().then(setIntegrations);
  }, []);

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Integrations
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 29 External Integrations Engine</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {integrations.map((item) => (
          <div key={item.id} className="glass-card" style={{ padding: '14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <Link2 size={16} style={{ color: 'var(--primary)' }} />
              <div>
                <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>{item.name}</div>
                <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{item.category}</div>
              </div>
            </div>
            <span className="status-badge" style={{ fontSize: '10px', background: 'rgba(34, 197, 94, 0.2)', color: 'var(--status-online)' }}>
              <CheckCircle2 size={10} /> Active
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
