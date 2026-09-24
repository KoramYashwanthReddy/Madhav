import React from 'react';
import { useWebApp } from '../context/WebAppContext';
import {
  MessageSquare,
  CheckSquare,
  Clock,
  Brain,
  Bot,
  Activity,
  ShieldCheck,
  Zap,
  ArrowRight,
} from 'lucide-react';

export const HomeView: React.FC = () => {
  const { setActiveSection, health, pendingApprovals, unreadCount } = useWebApp();

  return (
    <div className="view-container">
      {/* Welcome Banner */}
      <div className="glass-panel" style={{ padding: '24px 30px', background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.1) 100%)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h2 className="gradient-text" style={{ fontFamily: 'var(--font-heading)', fontSize: '24px', fontWeight: 800, marginBottom: '6px' }}>
              Welcome back to MAX Operating Layer
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px', maxWidth: '600px' }}>
              Your personal AI assistant runtime is active with 34 modules loaded. How can MAX assist your workflow today?
            </p>
          </div>
          <button
            onClick={() => setActiveSection('chat')}
            className="btn btn-primary"
            style={{ padding: '12px 20px', fontSize: '14px' }}
          >
            <MessageSquare size={18} />
            <span>Open Chat Workspace</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="glass-card metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-title">Backend Status</span>
            <ShieldCheck size={18} style={{ color: 'var(--status-online)' }} />
          </div>
          <div className="metric-value" style={{ color: 'var(--status-online)' }}>
            {health?.status === 'ok' ? 'Healthy' : 'Connecting'}
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
            {health ? `${health.active_modules} Modules Loaded` : 'Checking status...'}
          </span>
        </div>

        <div className="glass-card metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-title">Pending Approvals</span>
            <Zap size={18} style={{ color: pendingApprovals.length > 0 ? 'var(--status-danger)' : 'var(--primary)' }} />
          </div>
          <div className="metric-value">
            {pendingApprovals.length}
          </div>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
            {pendingApprovals.length > 0 ? 'Security authorization required' : 'No pending security requests'}
          </span>
        </div>

        <div className="glass-card metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-title">Active AI Agents</span>
            <Bot size={18} style={{ color: 'var(--accent-cyan)' }} />
          </div>
          <div className="metric-value">4 Agents</div>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>Computer, Filesystem, Terminal, Browser</span>
        </div>

        <div className="glass-card metric-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="metric-title">Proactive Alerts</span>
            <Activity size={18} style={{ color: 'var(--accent-purple)' }} />
          </div>
          <div className="metric-value">{unreadCount} Unread</div>
          <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>Proactive Intelligence & System Log</span>
        </div>
      </div>

      {/* Quick Launch Action Grid */}
      <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', marginTop: '8px' }}>
        Quick Access Workspaces
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        <div
          onClick={() => setActiveSection('tasks')}
          className="glass-card"
          style={{ padding: '20px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '10px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--primary)' }}>
              <CheckSquare size={20} />
            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>Task Engine</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
            Inspect multi-agent workflows, long-running goals, and step execution logs.
          </p>
        </div>

        <div
          onClick={() => setActiveSection('memory')}
          className="glass-card"
          style={{ padding: '20px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '10px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(168, 85, 247, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-purple)' }}>
              <Brain size={20} />
            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>Memory Engine</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
            Query long-term user preferences, stored facts, and semantic memory tags.
          </p>
        </div>

        <div
          onClick={() => setActiveSection('automations')}
          className="glass-card"
          style={{ padding: '20px', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: '10px' }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'rgba(236, 72, 153, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-pink)' }}>
              <Clock size={20} />
            </div>
            <ArrowRight size={16} style={{ color: 'var(--text-muted)' }} />
          </div>
          <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>Automations</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>
            View scheduled cron triggers, background monitoring tasks, and automated jobs.
          </p>
        </div>
      </div>
    </div>
  );
};
