import React from 'react';
import { useAdmin } from '../context/AdminContext';
import { AdminRole } from '../types';
import { Settings, Shield, UserCheck, Eye } from 'lucide-react';

export const SettingsView: React.FC = () => {
  const { adminRole, setAdminRole, isReadOnly, setIsReadOnly } = useAdmin();

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Admin Console Settings
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Session Security, Operational Modes & Preferences</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '640px' }}>
        {/* Role Selector */}
        <div className="admin-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UserCheck size={16} style={{ color: 'var(--primary)' }} />
            <h4 style={{ fontSize: '13px', fontWeight: 600, margin: 0 }}>Administrative Role Context</h4>
          </div>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
            Module 15 Security Engine enforces RBAC privileges authoritatively on backend.
          </p>

          <select
            value={adminRole}
            onChange={(e) => setAdminRole(e.target.value as AdminRole)}
            className="input-field"
          >
            <option value="SUPER_ADMIN">SUPER_ADMIN (Full Administrative Access)</option>
            <option value="SYSTEM_ADMIN">SYSTEM_ADMIN (Platform Operations)</option>
            <option value="OPERATOR">OPERATOR (Task & Tool Monitor)</option>
            <option value="READ_ONLY_ADMIN">READ_ONLY_ADMIN (Inspection Only)</option>
          </select>
        </div>

        {/* Read Only Toggle */}
        <div className="admin-panel" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Eye size={18} style={{ color: 'var(--accent-cyan)' }} />
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>Read-Only Mode</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Disables operational mutations in Admin Console</div>
            </div>
          </div>
          <button
            onClick={() => setIsReadOnly(!isReadOnly)}
            className={isReadOnly ? 'btn btn-primary' : 'btn btn-secondary'}
          >
            {isReadOnly ? 'Enabled' : 'Disabled'}
          </button>
        </div>
      </div>
    </div>
  );
};
