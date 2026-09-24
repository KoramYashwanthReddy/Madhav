import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { deviceCapabilityService } from '../services/DeviceCapabilityService';
import { Smartphone, BatteryCharging, Wifi, ShieldCheck, Trash2 } from 'lucide-react';

export const DeviceView: React.FC = () => {
  const { deviceInfo } = useMobileApp();

  const capabilities = [
    'BATTERY_STATUS',
    'NETWORK_STATUS',
    'SHOW_NOTIFICATION',
    'OPEN_URL',
    'CLIPBOARD',
    'FILE_PICKER',
    'OPEN_APP',
    'LOCATION',
    'CONTACTS_READ',
    'CALENDAR_READ',
  ] as const;

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Device Identity & Mobile Agent
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Backend Registered Device Telemetry</span>
      </div>

      {deviceInfo && (
        <div className="glass-panel" style={{ padding: '16px', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ padding: '10px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary)' }}>
              <Smartphone size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 700, margin: 0, color: 'var(--text-main)' }}>{deviceInfo.device_name}</h3>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ID: {deviceInfo.device_id}</span>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px', borderTop: '1px solid var(--border-glass)', paddingTop: '10px' }}>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>Platform:</span>
              <strong style={{ display: 'block', color: 'var(--text-main)' }}>{deviceInfo.platform.toUpperCase()} ({deviceInfo.os_version})</strong>
            </div>
            <div>
              <span style={{ color: 'var(--text-muted)' }}>App Version:</span>
              <strong style={{ display: 'block', color: 'var(--text-main)' }}>{deviceInfo.app_version}</strong>
            </div>
          </div>
        </div>
      )}

      {/* Capability List */}
      <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: '4px 0 0 0' }}>
        Mobile Agent OS Capability Status
      </h4>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {capabilities.map((cap) => {
          const state = deviceCapabilityService.getPermissionState(cap);
          return (
            <div key={cap} className="glass-card" style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px' }}>
              <code style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{cap}</code>
              <span
                style={{
                  fontSize: '10px',
                  fontWeight: 600,
                  padding: '2px 6px',
                  borderRadius: '4px',
                  background: state === 'supported' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255,255,255,0.06)',
                  color: state === 'supported' ? 'var(--status-online)' : 'var(--text-muted)',
                }}
              >
                {state.toUpperCase()}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
