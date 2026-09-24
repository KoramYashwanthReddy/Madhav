import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { MobileView } from '../types';
import {
  Mic,
  Brain,
  BookOpen,
  Clock,
  Activity,
  Link2,
  User,
  Settings,
  Smartphone,
  HelpCircle,
  X,
  LucideIcon,
} from 'lucide-react';

interface MoreItemDef {
  id: MobileView;
  label: string;
  category: string;
  icon: LucideIcon;
}

const moreItems: MoreItemDef[] = [
  { id: 'voice', label: 'Voice Assistant', category: 'Interaction', icon: Mic },
  { id: 'memory', label: 'Memory Engine', category: 'Core Knowledge', icon: Brain },
  { id: 'knowledge', label: 'Personal Knowledge', category: 'Core Knowledge', icon: BookOpen },
  { id: 'automations', label: 'Automations', category: 'Workflow', icon: Clock },
  { id: 'activity', label: 'Audit Activity', category: 'Observability', icon: Activity },
  { id: 'integrations', label: 'Integrations', category: 'Services', icon: Link2 },
  { id: 'profile', label: 'Identity Profile', category: 'System', icon: User },
  { id: 'settings', label: 'Settings & Autonomy', category: 'System', icon: Settings },
  { id: 'device', label: 'Device Management', category: 'Device', icon: Smartphone },
  { id: 'help', label: 'Help & About', category: 'System', icon: HelpCircle },
];

export const MoreDrawerModal: React.FC = () => {
  const { isMoreDrawerOpen, setIsMoreDrawerOpen, setActiveMoreView, activeMoreView } = useMobileApp();

  if (!isMoreDrawerOpen) return null;

  const handleSelect = (viewId: MobileView) => {
    setActiveMoreView(viewId);
    setIsMoreDrawerOpen(false);
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 900,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'flex-end',
      }}
      onClick={() => setIsMoreDrawerOpen(false)}
    >
      <div
        className="glass-panel"
        style={{
          maxHeight: '85vh',
          borderBottom: 0,
          borderLeft: 0,
          borderRight: 0,
          borderRadius: 'var(--radius-xl) var(--radius-xl) 0 0',
          display: 'flex',
          flexDirection: 'column',
          padding: '20px 16px',
          gap: '12px',
          overflowY: 'auto',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: '8px', borderBottom: '1px solid var(--border-glass)' }}>
          <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '16px', fontWeight: 700, margin: 0 }}>
            Workspaces & Device Options
          </h3>
          <button
            onClick={() => setIsMoreDrawerOpen(false)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '10px', marginTop: '6px' }}>
          {moreItems.map((item) => {
            const IconComp = item.icon;
            const isSelected = activeMoreView === item.id;
            return (
              <div
                key={item.id}
                onClick={() => handleSelect(item.id)}
                className="glass-card"
                style={{
                  padding: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  cursor: 'pointer',
                  borderColor: isSelected ? 'var(--primary)' : undefined,
                  background: isSelected ? 'rgba(99, 102, 241, 0.15)' : undefined,
                }}
              >
                <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(255,255,255,0.06)', color: 'var(--primary)' }}>
                  <IconComp size={18} />
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)' }}>{item.label}</div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{item.category}</div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
