import React, { useState, useEffect } from 'react';
import { useAdmin } from '../context/AdminContext';
import { RegisteredDevice } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Smartphone, Monitor, Globe, Trash2 } from 'lucide-react';

export const DevicesView: React.FC = () => {
  const { openDangerousActionModal } = useAdmin();
  const [devices, setDevices] = useState<RegisteredDevice[]>([]);

  useEffect(() => {
    adminApiClient.getDevices().then(setDevices);
  }, []);

  const handleRevokeDevice = (device: RegisteredDevice) => {
    openDangerousActionModal(
      'Revoke Registered Client Device',
      `Are you sure you want to revoke registration for "${device.name}" (${device.device_id})? Active sessions will be terminated immediately.`,
      'REVOKE_DEVICE',
      device.device_id,
      async () => {
        await adminApiClient.revokeDevice(device.device_id);
        const updated = await adminApiClient.getDevices();
        setDevices(updated);
      }
    );
  };

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Client Device & Session Manager
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Modules 34 (Desktop), 35 (Web), 36 (Mobile) Client Registry</span>
      </div>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Client Type</th>
              <th>Device Name</th>
              <th>Device ID</th>
              <th>Platform / OS</th>
              <th>App Version</th>
              <th>Last Seen</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.device_id}>
                <td>
                  <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}>
                    {d.client_type === 'desktop' && <Monitor size={14} style={{ color: 'var(--primary)' }} />}
                    {d.client_type === 'web' && <Globe size={14} style={{ color: 'var(--accent-cyan)' }} />}
                    {d.client_type === 'mobile' && <Smartphone size={14} style={{ color: 'var(--accent-purple)' }} />}
                    {d.client_type.toUpperCase()}
                  </span>
                </td>
                <td style={{ fontWeight: 600 }}>{d.name}</td>
                <td style={{ fontFamily: 'var(--font-mono)', fontSize: '11px' }}>{d.device_id}</td>
                <td>{d.platform}</td>
                <td>{d.app_version}</td>
                <td>{new Date(d.last_seen).toLocaleTimeString()}</td>
                <td>
                  <span className="admin-status-badge">
                    <span className={`status-dot ${d.status === 'active' ? 'healthy' : 'danger'}`} />
                    <span>{d.status.toUpperCase()}</span>
                  </span>
                </td>
                <td>
                  <button
                    onClick={() => handleRevokeDevice(d)}
                    className="btn btn-danger"
                    style={{ padding: '3px 8px', fontSize: '10px' }}
                  >
                    <Trash2 size={12} />
                    <span>Revoke</span>
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
