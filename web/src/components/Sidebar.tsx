import React from 'react';
import { useWebApp } from '../context/WebAppContext';
import { NavSection } from '../types';
import {
  Home,
  MessageSquare,
  CheckSquare,
  Clock,
  Brain,
  BookOpen,
  Bot,
  Wrench,
  Link2,
  Bell,
  Activity,
  Award,
  Cpu,
  Settings,
  LucideIcon,
} from 'lucide-react';

interface NavItemDef {
  id: NavSection;
  label: string;
  icon: LucideIcon;
  badge?: string;
}

const navItems: NavItemDef[] = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'tasks', label: 'Tasks', icon: CheckSquare },
  { id: 'automations', label: 'Automations', icon: Clock },
  { id: 'memory', label: 'Memory', icon: Brain },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
  { id: 'agents', label: 'Agents', icon: Bot },
  { id: 'tools', label: 'Tools', icon: Wrench },
  { id: 'integrations', label: 'Integrations', icon: Link2 },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'activity', label: 'Activity', icon: Activity },
  { id: 'evaluations', label: 'Evaluations', icon: Award },
  { id: 'system', label: 'System', icon: Cpu },
  { id: 'settings', label: 'Settings', icon: Settings },
];

export const Sidebar: React.FC = () => {
  const { activeSection, setActiveSection, unreadCount, pendingApprovals } = useWebApp();

  return (
    <aside
      className="glass-panel"
      style={{
        width: '240px',
        borderRadius: 0,
        borderTop: 0,
        borderBottom: 0,
        borderLeft: 0,
        display: 'flex',
        flexDirection: 'column',
        padding: '16px 12px',
        gap: '4px',
        overflowY: 'auto',
      }}
      aria-label="Main Navigation Sidebar"
    >
      <div style={{ padding: '4px 12px 12px 12px', fontSize: '11px', fontWeight: 600, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Navigation Workspace
      </div>

      {navItems.map((item) => {
        const IconComponent = item.icon;
        const isActive = activeSection === item.id;
        
        let badgeContent: number | undefined;
        if (item.id === 'notifications' && unreadCount > 0) {
          badgeContent = unreadCount;
        } else if (item.id === 'system' && pendingApprovals.length > 0) {
          badgeContent = pendingApprovals.length;
        }

        return (
          <button
            key={item.id}
            onClick={() => setActiveSection(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid',
              borderColor: isActive ? 'var(--primary-glow)' : 'transparent',
              background: isActive
                ? 'linear-gradient(90deg, rgba(99, 102, 241, 0.2) 0%, rgba(99, 102, 241, 0.05) 100%)'
                : 'transparent',
              color: isActive ? 'var(--text-main)' : 'var(--text-muted)',
              fontWeight: isActive ? 600 : 400,
              fontSize: '13px',
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all var(--transition-fast)',
            }}
            aria-current={isActive ? 'page' : undefined}
          >
            <IconComponent size={18} style={{ color: isActive ? 'var(--primary)' : 'inherit' }} />
            <span style={{ flex: 1 }}>{item.label}</span>
            {badgeContent !== undefined && badgeContent > 0 && (
              <span
                style={{
                  background: item.id === 'system' ? 'var(--status-danger)' : 'var(--primary)',
                  color: '#fff',
                  fontSize: '10px',
                  fontWeight: 700,
                  padding: '2px 6px',
                  borderRadius: '999px',
                }}
              >
                {badgeContent}
              </span>
            )}
          </button>
        );
      })}
    </aside>
  );
};
