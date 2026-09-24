import React from 'react';
import { useAdmin } from '../context/AdminContext';
import { AdminSection } from '../types';
import {
  LayoutDashboard,
  Cpu,
  Database,
  Bot,
  Wrench,
  Shield,
  CheckSquare,
  Clock,
  Smartphone,
  Link2,
  Bell,
  Activity,
  FileText,
  Award,
  Sliders,
  Stethoscope,
  Settings,
  LucideIcon,
} from 'lucide-react';

interface SidebarItem {
  id: AdminSection;
  label: string;
  category: 'Core' | 'Operations' | 'Security & Audit' | 'System';
  icon: LucideIcon;
}

const sidebarItems: SidebarItem[] = [
  { id: 'dashboard', label: 'Dashboard', category: 'Core', icon: LayoutDashboard },
  { id: 'runtime', label: 'AI Runtime', category: 'Core', icon: Cpu },
  { id: 'models', label: 'Models', category: 'Core', icon: Database },
  { id: 'agents', label: 'Agents', category: 'Operations', icon: Bot },
  { id: 'tools', label: 'Tools', category: 'Operations', icon: Wrench },
  { id: 'security', label: 'Security Engine', category: 'Security & Audit', icon: Shield },
  { id: 'tasks', label: 'Task Monitor', category: 'Operations', icon: CheckSquare },
  { id: 'automations', label: 'Automations', category: 'Operations', icon: Clock },
  { id: 'devices', label: 'Device Manager', category: 'Operations', icon: Smartphone },
  { id: 'integrations', label: 'Integrations', category: 'Operations', icon: Link2 },
  { id: 'notifications', label: 'Notifications', category: 'Operations', icon: Bell },
  { id: 'observability', label: 'Observability', category: 'Security & Audit', icon: Activity },
  { id: 'audit', label: 'Audit Logs', category: 'Security & Audit', icon: FileText },
  { id: 'evaluations', label: 'Evaluations', category: 'System', icon: Award },
  { id: 'configuration', label: 'Configuration', category: 'System', icon: Sliders },
  { id: 'diagnostics', label: 'Diagnostics', category: 'System', icon: Stethoscope },
  { id: 'settings', label: 'Admin Settings', category: 'System', icon: Settings },
];

export const AdminSidebar: React.FC = () => {
  const { activeSection, setActiveSection, alerts } = useAdmin();

  return (
    <aside
      className="admin-panel"
      style={{
        width: '230px',
        borderRadius: 0,
        borderTop: 0,
        borderBottom: 0,
        borderLeft: 0,
        display: 'flex',
        flexDirection: 'column',
        padding: '12px 8px',
        gap: '2px',
        overflowY: 'auto',
      }}
      aria-label="Admin Navigation Sidebar"
    >
      <div style={{ padding: '4px 10px 8px 10px', fontSize: '10px', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        Console Sections
      </div>

      {sidebarItems.map((item) => {
        const IconComp = item.icon;
        const isActive = activeSection === item.id;

        return (
          <button
            key={item.id}
            onClick={() => setActiveSection(item.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              padding: '8px 10px',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid',
              borderColor: isActive ? 'var(--primary)' : 'transparent',
              background: isActive ? 'rgba(59, 130, 246, 0.15)' : 'transparent',
              color: isActive ? 'var(--text-main)' : 'var(--text-muted)',
              fontWeight: isActive ? 600 : 400,
              fontSize: '12px',
              cursor: 'pointer',
              textAlign: 'left',
            }}
            aria-current={isActive ? 'page' : undefined}
          >
            <IconComp size={16} style={{ color: isActive ? 'var(--primary)' : 'inherit' }} />
            <span style={{ flex: 1 }}>{item.label}</span>
          </button>
        );
      })}
    </aside>
  );
};
