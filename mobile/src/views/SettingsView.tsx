import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { Settings, Shield, Fingerprint, Wifi, Moon, Eye } from 'lucide-react';

export const SettingsView: React.FC = () => {
  const { autonomyLevel, setAutonomyLevel, connectionMode, setConnectionMode, isBiometricLocked } = useMobileApp();

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Mobile Settings
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Autonomy Policy, Security & Preferences</span>
      </div>

      {/* Autonomy Level Slider / Selector (Levels 0 - 5) */}
      <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Shield size={18} style={{ color: 'var(--primary)' }} />
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: 0 }}>Autonomy Level: {autonomyLevel}</h4>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
          {autonomyLevel === 0 && 'Level 0 — Suggest only'}
          {autonomyLevel === 1 && 'Level 1 — Ask before actions'}
          {autonomyLevel === 2 && 'Level 2 — Limited approved actions'}
          {autonomyLevel === 3 && 'Level 3 — Routine automation'}
          {autonomyLevel === 4 && 'Level 4 — Expanded autonomy'}
          {autonomyLevel === 5 && 'Level 5 — Advanced autonomy'}
        </p>
        <input
          type="range"
          min="0"
          max="5"
          value={autonomyLevel}
          onChange={(e) => setAutonomyLevel(parseInt(e.target.value, 10))}
          style={{ width: '100%', accentColor: 'var(--primary)' }}
        />
      </div>

      {/* Connection Mode Selection */}
      <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Wifi size={18} style={{ color: 'var(--accent-cyan)' }} />
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: 0 }}>Connection Mode</h4>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
          {(['LOCAL', 'REMOTE', 'OFFLINE'] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setConnectionMode(mode)}
              className="glass-card"
              style={{
                padding: '8px',
                fontSize: '11px',
                fontWeight: 700,
                textAlign: 'center',
                cursor: 'pointer',
                borderColor: connectionMode === mode ? 'var(--primary)' : undefined,
                background: connectionMode === mode ? 'rgba(99, 102, 241, 0.2)' : undefined,
                color: connectionMode === mode ? 'var(--text-main)' : 'var(--text-muted)',
              }}
            >
              {mode}
            </button>
          ))}
        </div>
      </div>

      {/* Biometric Security */}
      <div className="glass-card" style={{ padding: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Fingerprint size={18} style={{ color: 'var(--accent-purple)' }} />
          <div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>Biometric App Protection</div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Fingerprint / Face ID local unlock</div>
          </div>
        </div>
        <span className="status-badge" style={{ fontSize: '10px' }}>
          {isBiometricLocked ? 'Locked' : 'Active'}
        </span>
      </div>
    </div>
  );
};
