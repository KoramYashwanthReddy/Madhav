import React, { useState, useEffect } from 'react';
import { IntegrationStatus } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Link2 } from 'lucide-react';

export const IntegrationsView: React.FC = () => {
  const [integrations, setIntegrations] = useState<IntegrationStatus[]>([]);

  useEffect(() => {
    adminApiClient.getIntegrations().then(setIntegrations);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          External Service Integrations
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 29 External Service Connectors</span>
      </div>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Integration Name</th>
              <th>Category</th>
              <th>Auth Status</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {integrations.map((item) => (
              <tr key={item.id}>
                <td style={{ fontWeight: 600 }}>{item.name}</td>
                <td>{item.category}</td>
                <td>{item.auth_status}</td>
                <td>
                  <span className="admin-status-badge">
                    <span className={`status-dot ${item.connected ? 'healthy' : 'danger'}`} />
                    <span>{item.connected ? 'CONNECTED' : 'DISCONNECTED'}</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
