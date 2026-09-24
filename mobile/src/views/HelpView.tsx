import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { HelpCircle, Info, ShieldCheck, CheckCircle2 } from 'lucide-react';

export const HelpView: React.FC = () => {
  const { health } = useMobileApp();

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Help & Protocol Version
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>MAX Personal AI Operating Layer</span>
      </div>

      <div className="glass-panel" style={{ padding: '16px', borderRadius: 'var(--radius-lg)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Info size={18} style={{ color: 'var(--primary)' }} />
          <h4 style={{ fontSize: '14px', fontWeight: 600, margin: 0 }}>Version Compatibility Matrix</h4>
        </div>

        <div style={{ fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px', color: 'var(--text-muted)' }}>
          <div>Client Version: <strong style={{ color: 'var(--text-main)' }}>1.0.0-module36</strong></div>
          <div>Backend Protocol: <strong style={{ color: 'var(--text-main)' }}>v1.0 (Modules 01–36)</strong></div>
          <div>Active Modules: <strong style={{ color: 'var(--status-online)' }}>{health?.active_modules || 35} Loaded</strong></div>
        </div>
      </div>

      <div className="glass-card" style={{ padding: '14px', fontSize: '12px', color: 'var(--text-muted)', lineHeight: 1.5 }}>
        <strong style={{ color: 'var(--text-main)', display: 'block', marginBottom: '4px' }}>Architectural Boundaries:</strong>
        The Mobile App acts strictly as a client UI. AI reasoning, memory retrieval, RAG, agent orchestration, and tool execution permissions are handled authoritatively by the Python backend.
      </div>
    </div>
  );
};
