import React from 'react';
import { useMobileApp } from '../context/MobileAppContext';
import { BottomTab } from '../types';
import { Home, MessageSquare, CheckSquare, Bell, MoreHorizontal, LucideIcon } from 'lucide-react';

interface TabDef {
  id: BottomTab;
  label: string;
  icon: LucideIcon;
}

const tabs: TabDef[] = [
  { id: 'home', label: 'Home', icon: Home },
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'tasks', label: 'Tasks', icon: CheckSquare },
  { id: 'notifications', label: 'Alerts', icon: Bell },
  { id: 'more', label: 'More', icon: MoreHorizontal },
];

export const BottomNavigation: React.FC = () => {
  const { activeTab, setActiveTab, unreadCount, setIsMoreDrawerOpen } = useMobileApp();

  const handleTabClick = (tabId: BottomTab) => {
    setActiveTab(tabId);
    if (tabId === 'more') {
      setIsMoreDrawerOpen(true);
    }
  };

  return (
    <nav className="bottom-nav-bar" aria-label="Bottom Navigation Bar">
      {tabs.map((t) => {
        const IconComp = t.icon;
        const isActive = activeTab === t.id;

        return (
          <button
            key={t.id}
            onClick={() => handleTabClick(t.id)}
            className={`bottom-tab-item ${isActive ? 'active' : ''}`}
            aria-label={t.label}
          >
            <IconComp size={20} />
            <span>{t.label}</span>
            {t.id === 'notifications' && unreadCount > 0 && (
              <span
                style={{
                  position: 'absolute',
                  top: '6px',
                  right: '24%',
                  width: '14px',
                  height: '14px',
                  borderRadius: '50%',
                  background: 'var(--status-danger)',
                  color: '#fff',
                  fontSize: '9px',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {unreadCount}
              </span>
            )}
          </button>
        );
      })}
    </nav>
  );
};
