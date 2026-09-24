import React, { useState, useEffect } from 'react';
import { AutomationJob } from '../types';
import { mobileApiClient } from '../api/client';
import { Clock, Play, Pause } from 'lucide-react';

export const AutomationsView: React.FC = () => {
  const [jobs, setJobs] = useState<AutomationJob[]>([]);

  useEffect(() => {
    mobileApiClient.getAutomations().then(setJobs);
  }, []);

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Automations
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 28 Scheduler & Trigger Engine</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {jobs.map((job) => (
          <div key={job.id} className="glass-card" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={16} style={{ color: 'var(--accent-pink)' }} />
                <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{job.name}</h4>
              </div>
              <span className="status-badge" style={{ fontSize: '10px' }}>
                {job.enabled ? 'Active' : 'Paused'}
              </span>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{job.description}</p>

            <div style={{ fontSize: '11px', color: 'var(--text-dim)', fontFamily: 'var(--font-mono)' }}>
              Cron: {job.cron_expression} • Target: {job.target_tool}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
