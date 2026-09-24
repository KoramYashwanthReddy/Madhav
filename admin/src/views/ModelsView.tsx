import React, { useState, useEffect } from 'react';
import { ModelInfo } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Database, CheckCircle2, XCircle } from 'lucide-react';

export const ModelsView: React.FC = () => {
  const [models, setModels] = useState<ModelInfo[]>([]);

  useEffect(() => {
    adminApiClient.getModels().then(setModels);
  }, []);

  const toggleModel = async (id: string, current: boolean) => {
    const updated = await adminApiClient.toggleModel(id, !current);
    setModels((prev) => prev.map((m) => (m.id === id ? updated : m)));
  };

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Model Registry & Lifecycle
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 05 Model Management & Availability</span>
      </div>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Model Name</th>
              <th>Provider</th>
              <th>Version</th>
              <th>Format</th>
              <th>Checksum</th>
              <th>Latency</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m) => (
              <tr key={m.id}>
                <td style={{ fontWeight: 600 }}>{m.name}</td>
                <td>{m.provider}</td>
                <td>{m.version}</td>
                <td>{m.format}</td>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-dim)' }}>{m.checksum}</td>
                <td>{m.latency_ms}ms</td>
                <td>
                  <span className="admin-status-badge">
                    <span className={`status-dot ${m.active ? 'healthy' : 'danger'}`} />
                    <span>{m.active ? 'ACTIVE' : 'INACTIVE'}</span>
                  </span>
                </td>
                <td>
                  <button
                    onClick={() => toggleModel(m.id, m.active)}
                    className={m.active ? 'btn btn-secondary' : 'btn btn-primary'}
                    style={{ padding: '3px 8px', fontSize: '10px' }}
                  >
                    {m.active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
