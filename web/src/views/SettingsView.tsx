import React from 'react';
import { useWebApp } from '../context/WebAppContext';
import { AutonomyLevel } from '../types';
import { Settings, Shield, Sliders, Eye, Volume2 } from 'lucide-react';

export const SettingsView: React.FC = () => {
  const { preferences, updatePreferences } = useWebApp();

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          User Preferences & Autonomy Policy
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 02 Configuration, Module 03 Identity Profile & Module 15 Security
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', maxWidth: '720px' }}>
        {/* Autonomy Level Control */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Shield size={20} style={{ color: 'var(--primary)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 600, margin: 0 }}>Execution Autonomy Level</h3>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>
            Configure how much independence MAX agents possess when performing filesystem, terminal, or computer control actions.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', marginTop: '6px' }}>
            {(['strict', 'guarded', 'autonomous'] as AutonomyLevel[]).map((level) => (
              <button
                key={level}
                type="button"
                onClick={() => updatePreferences({ autonomy_level: level })}
                className="glass-card"
                style={{
                  padding: '14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  textAlign: 'left',
                  cursor: 'pointer',
                  borderColor: preferences.autonomy_level === level ? 'var(--primary)' : undefined,
                  background: preferences.autonomy_level === level ? 'rgba(99, 102, 241, 0.15)' : undefined,
                }}
              >
                <span style={{ fontSize: '14px', fontWeight: 700, textTransform: 'capitalize', color: 'var(--text-main)' }}>
                  {level}
                </span>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {level === 'strict'
                    ? 'All actions require explicit user approval'
                    : level === 'guarded'
                    ? 'Medium & high risk actions require approval'
                    : 'Full autonomy for all tool actions'}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* API Endpoint & Model Selection */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sliders size={20} style={{ color: 'var(--accent-purple)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 600, margin: 0 }}>API & Model Settings</h3>
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>MAX Backend API Endpoint URL</label>
            <input
              type="text"
              value={preferences.api_endpoint}
              onChange={(e) => updatePreferences({ api_endpoint: e.target.value })}
              className="input-field"
              style={{ marginTop: '4px' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 600 }}>Default LLM Reasoning Model</label>
            <select
              value={preferences.primary_model}
              onChange={(e) => updatePreferences({ primary_model: e.target.value })}
              className="input-field"
              style={{ marginTop: '4px' }}
            >
              <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
              <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
              <option value="ollama-llama3">Local Ollama Llama3</option>
            </select>
          </div>
        </div>

        {/* Accessibility & UX Settings */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Eye size={20} style={{ color: 'var(--accent-cyan)' }} />
            <h3 style={{ fontSize: '16px', fontWeight: 600, margin: 0 }}>Accessibility & UI Customization</h3>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', display: 'block' }}>High Contrast Theme</span>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Maximize text contrast for screen visibility</span>
            </div>
            <button
              onClick={() => updatePreferences({ theme: preferences.theme === 'high-contrast' ? 'glass' : 'high-contrast' })}
              className="btn btn-secondary"
              style={{ padding: '6px 12px', fontSize: '12px' }}
            >
              {preferences.theme === 'high-contrast' ? 'Enabled' : 'Disabled'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
