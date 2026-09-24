import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import {
  MessageSquare,
  CheckSquare,
  Clock,
  Mic,
  Smartphone,
  ShieldCheck,
  Zap,
  ArrowRight,
  BatteryCharging,
  Wifi,
} from 'lucide-react';

export const HomeView: React.FC = () => {
  const {
    setActiveTab,
    setActiveMoreView,
    health,
    deviceInfo,
    pendingApprovals,
    unreadCount,
    connectionMode,
  } = useMobileApp();

  const handleOpenMore = (view: 'automations' | 'voice' | 'device') => {
    setActiveMoreView(view);
    setActiveTab('more');
  };

  return (
    <div className="mobile-view-container">
      {/* Mobile Command Banner */}
      <div className="glass-panel" style={{ padding: '20px', borderRadius: 'var(--radius-lg)', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.18) 0%, rgba(168, 85, 247, 0.12) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--accent-cyan)', letterSpacing: '0.5px' }}>
            Mobile Command Center
          </span>
          <span className="status-badge" style={{ background: 'rgba(0,0,0,0.3)' }}>
            <span className={`status-dot ${health?.status === 'ok' ? 'online' : 'danger'}`} />
            <span>{health ? `${health.active_modules} Modules` : 'Connecting'}</span>
          </span>
        </div>

        <h2 className="gradient-text" style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 800, margin: '0 0 6px 0' }}>
          MAX Personal AI
        </h2>

        <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
          Connected via {connectionMode} mode. Voice & Mobile Agent ready.
        </p>

        <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
          <button
            onClick={() => setActiveTab('chat')}
            className="btn btn-primary"
            style={{ flex: 1, minHeight: '40px', fontSize: '13px' }}
          >
            <MessageSquare size={16} />
            <span>Open Chat</span>
          </button>

          <button
            onClick={() => handleOpenMore('voice')}
            className="btn btn-secondary"
            style={{ flex: 1, minHeight: '40px', fontSize: '13px' }}
          >
            <Mic size={16} />
            <span>Voice Mode</span>
          </button>
        </div>
      </div>

      {/* Device & Security Quick Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div className="glass-card" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Battery & Net</span>
            <BatteryCharging size={16} style={{ color: 'var(--status-online)' }} />
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-main)' }}>
            {deviceInfo ? `${Math.round(deviceInfo.battery_level * 100)}%` : '88%'}
          </div>
          <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
            {deviceInfo?.network_type.toUpperCase() || 'WIFI'} • Charging
          </span>
        </div>

        <div className="glass-card" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Approvals</span>
            <Zap size={16} style={{ color: pendingApprovals.length > 0 ? 'var(--status-danger)' : 'var(--primary)' }} />
          </div>
          <div style={{ fontSize: '16px', fontWeight: 700, color: pendingApprovals.length > 0 ? 'var(--status-danger)' : 'var(--text-main)' }}>
            {pendingApprovals.length} Pending
          </div>
          <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
            Module 15 Security
          </span>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <h4 style={{ fontFamily: 'var(--font-heading)', fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: '4px 0 0 0' }}>
        Workspaces
      </h4>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div
          onClick={() => setActiveTab('tasks')}
          className="glass-card"
          style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary)' }}>
              <CheckSquare size={18} />
            </div>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>Active Tasks</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>1 task running in background</div>
            </div>
          </div>
          <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />
        </div>

        <div
          onClick={() => handleOpenMore('automations')}
          className="glass-card"
          style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(236, 72, 153, 0.15)', color: 'var(--accent-pink)' }}>
              <Clock size={18} />
            </div>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>Scheduled Automations</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Daily morning briefing active</div>
            </div>
          </div>
          <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />
        </div>

        <div
          onClick={() => handleOpenMore('device')}
          className="glass-card"
          style={{ padding: '14px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(187, 92, 255, 0.15)', color: 'var(--accent-purple)' }}>
              <Smartphone size={18} />
            </div>
            <div>
              <div style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>Device Agent</div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Android 15 • 12 Capabilities</div>
            </div>
          </div>
          <ArrowRight size={16} style={{ color: 'var(--text-dim)' }} />
        </div>
      </div>
    </div>
  );
};
