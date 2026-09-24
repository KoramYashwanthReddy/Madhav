import React, { useState } from 'react';
import { DiagnosticResult } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Stethoscope, CheckCircle2, Play, AlertCircle } from 'lucide-react';

export const DiagnosticsView: React.FC = () => {
  const [results, setResults] = useState<DiagnosticResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const handleRunDiagnostics = async () => {
    setIsRunning(true);
    try {
      const res = await adminApiClient.runDiagnostics();
      setResults(res);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="admin-view-container">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
            Predefined Safe Diagnostics Suite
          </h2>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Automated Component Dependency & Capability Checks</span>
        </div>

        <button
          onClick={handleRunDiagnostics}
          disabled={isRunning}
          className="btn btn-primary"
        >
          <Play size={14} />
          <span>{isRunning ? 'Running Checks...' : 'Run Diagnostics'}</span>
        </button>
      </div>

      <div className="admin-panel" style={{ padding: '16px' }}>
        {results.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '12px' }}>
            Click "Run Diagnostics" above to execute predefined safe system capability checks.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {results.map((r) => (
              <div key={r.id} className="admin-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>{r.name} ({r.category})</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>{r.details}</div>
                </div>
                <span className="admin-status-badge">
                  <span className={`status-dot ${r.status === 'PASSED' ? 'healthy' : 'danger'}`} />
                  <span>{r.status}</span>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
