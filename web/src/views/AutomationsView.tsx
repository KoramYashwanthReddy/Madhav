import React, { useState, useEffect } from 'react';
import { AutomationJob } from '../types';
import { webApiClient } from '../api/client';
import { Clock, Play, Pause, RefreshCw, Zap } from 'lucide-react';

export const AutomationsView: React.FC = () => {
  const [jobs, setJobs] = useState<AutomationJob[]>([]);

  useEffect(() => {
    webApiClient.getAutomations().then(setJobs);
  }, []);

  const toggleJob = async (id: string, current: boolean) => {
    const updated = await webApiClient.toggleAutomation(id, !current);
    setJobs((prev) => prev.map((j) => (j.id === id ? updated : j)));
  };

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          Scheduler & Automation Jobs
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 28 Scheduler & Automation Engine
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '16px' }}>
        {jobs.map((job) => (
          <div key={job.id} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Clock size={18} style={{ color: 'var(--accent-pink)' }} />
                <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{job.name}</h4>
              </div>
              <button
                onClick={() => toggleJob(job.id, job.enabled)}
                className={job.enabled ? 'btn btn-primary' : 'btn btn-secondary'}
                style={{ padding: '4px 10px', fontSize: '11px' }}
              >
                {job.enabled ? <Pause size={12} /> : <Play size={12} />}
                <span>{job.enabled ? 'Active' : 'Paused'}</span>
              </button>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{job.description}</p>

            <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px 12px', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px', fontFamily: 'var(--font-mono)' }}>
              <span>Cron: {job.cron_expression}</span>
              <span style={{ color: 'var(--primary)' }}>{job.action_type}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-dim)' }}>
              <span>Last run: {job.last_run_at ? new Date(job.last_run_at).toLocaleDateString() : 'Never'}</span>
              <span>Target: {job.target_tool}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
