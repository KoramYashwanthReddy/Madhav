import React, { useState, useEffect } from 'react';
import { AutomationJob } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Clock } from 'lucide-react';

export const AutomationsView: React.FC = () => {
  const [jobs, setJobs] = useState<AutomationJob[]>([]);

  useEffect(() => {
    adminApiClient.getAutomations().then(setJobs);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Scheduler & Automation Jobs
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 28 Scheduler & Automation Engine Monitor</span>
      </div>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Name</th>
              <th>Cron Expression</th>
              <th>Target Tool</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((j) => (
              <tr key={j.id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{j.id}</td>
                <td>{j.name}</td>
                <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>{j.cron_expression}</td>
                <td style={{ fontFamily: 'var(--font-mono)' }}>{j.target_tool}</td>
                <td>
                  <span className="admin-status-badge">
                    <span className={`status-dot ${j.enabled ? 'healthy' : 'danger'}`} />
                    <span>{j.enabled ? 'ACTIVE' : 'PAUSED'}</span>
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
