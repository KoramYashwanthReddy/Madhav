import React from 'react';
import { useAdmin } from '../context/AdminContext';
import { ShieldCheck, Cpu, Bot, Wrench, CheckSquare, Clock, AlertTriangle, Activity } from 'lucide-react';

export const DashboardView: React.FC = () => {
  const { healthComponents, alerts, securityMode, setActiveSection } = useAdmin();

  return (
    <div className="admin-view-container">
      {/* Executive Status Header */}
      <div className="admin-panel" style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
            Executive Operational Dashboard
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '12px', margin: '4px 0 0 0' }}>
            MAX Personal AI Operating System — Modules 01–36 Complete
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div className="admin-status-badge" style={{ padding: '6px 12px', fontSize: '12px' }}>
            <span className={`status-dot ${securityMode === 'NORMAL' ? 'healthy' : 'danger'}`} />
            <span>Mode: {securityMode}</span>
          </div>
        </div>
      </div>

      {/* Component Health Matrix Grid */}
      <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: '4px 0 0 0' }}>
        System Component Health Matrix
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '12px' }}>
        {healthComponents.map((c) => (
          <div key={c.id} className="admin-card" style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
                {c.category}
              </span>
              <span className="admin-status-badge" style={{ fontSize: '10px' }}>
                <span className={`status-dot ${c.status === 'HEALTHY' ? 'healthy' : 'danger'}`} />
                <span>{c.status}</span>
              </span>
            </div>

            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{c.name}</h4>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-dim)', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '6px' }}>
              <span>Latency: {c.latency_ms}ms</span>
              <span>Checked: {new Date(c.last_check).toLocaleTimeString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Operational Alerts & Recent Activity */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '4px' }}>
        <div className="admin-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={16} style={{ color: 'hsl(38, 92%, 50%)' }} />
              <h4 style={{ fontSize: '13px', fontWeight: 600, margin: 0 }}>Operational Alerts</h4>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>{alerts.length} Active</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {alerts.map((alt) => (
              <div key={alt.id} className="admin-card" style={{ padding: '10px', fontSize: '12px' }}>
                <strong style={{ color: 'var(--text-main)', display: 'block' }}>{alt.title}</strong>
                <span style={{ color: 'var(--text-muted)' }}>{alt.message}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="admin-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Activity size={16} style={{ color: 'var(--primary)' }} />
              <h4 style={{ fontSize: '13px', fontWeight: 600, margin: 0 }}>Quick Section Jump</h4>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <button onClick={() => setActiveSection('runtime')} className="btn btn-secondary" style={{ justifyContent: 'flex-start' }}>
              <Cpu size={14} /> AI Runtime
            </button>
            <button onClick={() => setActiveSection('agents')} className="btn btn-secondary" style={{ justifyContent: 'flex-start' }}>
              <Bot size={14} /> Agent Engine
            </button>
            <button onClick={() => setActiveSection('tools')} className="btn btn-secondary" style={{ justifyContent: 'flex-start' }}>
              <Wrench size={14} /> Tool Registry
            </button>
            <button onClick={() => setActiveSection('security')} className="btn btn-secondary" style={{ justifyContent: 'flex-start' }}>
              <ShieldCheck size={14} /> Security Engine
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
