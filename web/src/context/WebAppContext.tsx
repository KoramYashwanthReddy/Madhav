import React, { createContext, useContext, useState, useEffect } from 'react';
import { NavSection, BackendHealth, SecurityApprovalRequest, UserPreferences, ProactiveNotification } from '../types';
import { webApiClient } from '../api/client';

interface WebAppContextType {
  activeSection: NavSection;
  setActiveSection: (section: NavSection) => void;
  health: BackendHealth | null;
  pendingApprovals: SecurityApprovalRequest[];
  notifications: ProactiveNotification[];
  unreadCount: number;
  isCommandPaletteOpen: boolean;
  setIsCommandPaletteOpen: (open: boolean) => void;
  isNotificationDrawerOpen: boolean;
  setIsNotificationDrawerOpen: (open: boolean) => void;
  preferences: UserPreferences;
  updatePreferences: (prefs: Partial<UserPreferences>) => void;
  handleApprovalResponse: (id: string, approved: boolean) => Promise<void>;
  markNotificationRead: (id: string) => void;
  refreshHealth: () => Promise<void>;
}

const defaultPreferences: UserPreferences = {
  theme: 'glass',
  autonomy_level: 'guarded',
  primary_model: 'gemini-1.5-pro',
  api_endpoint: 'http://127.0.0.1:8000/api/v1',
  enable_sound_effects: true,
  reduced_motion: false,
  voice_input_enabled: true,
  voice_output_enabled: true,
  auto_speak: false,
  selected_voice: '',
  speech_speed: 1.0,
  voice_language: 'en-US',
};

const WebAppContext = createContext<WebAppContextType | undefined>(undefined);

export const WebAppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeSection, setActiveSection] = useState<NavSection>('home');
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<SecurityApprovalRequest[]>([]);
  const [notifications, setNotifications] = useState<ProactiveNotification[]>([]);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [isNotificationDrawerOpen, setIsNotificationDrawerOpen] = useState(false);
  const [preferences, setPreferences] = useState<UserPreferences>(defaultPreferences);

  const refreshHealth = async () => {
    try {
      const h = await webApiClient.getHealth();
      setHealth(h);
    } catch {
      setHealth(null);
    }
  };

  const loadInitialData = async () => {
    await refreshHealth();
    try {
      const apps = await webApiClient.getPendingApprovals();
      setPendingApprovals(Array.isArray(apps) ? apps : []);
      const notifs = await webApiClient.getNotifications();
      setNotifications(Array.isArray(notifs) ? notifs : []);
    } catch {
      // API fallback handled in client
    }
  };

  useEffect(() => {
    loadInitialData();
    const interval = setInterval(refreshHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcut listener (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const updatePreferences = (prefs: Partial<UserPreferences>) => {
    setPreferences((prev) => {
      const updated = { ...prev, ...prefs };
      if (updated.theme === 'high-contrast') {
        document.documentElement.setAttribute('data-theme', 'high-contrast');
      } else {
        document.documentElement.removeAttribute('data-theme');
      }
      return updated;
    });
  };

  const handleApprovalResponse = async (id: string, approved: boolean) => {
    try {
      await webApiClient.respondApproval(id, approved);
    } catch {
      // Ignore network errors on response
    }
    setPendingApprovals((prev) => (Array.isArray(prev) ? prev.filter((a) => a.id !== id) : []));
  };

  const markNotificationRead = (id: string) => {
    setNotifications((prev) =>
      Array.isArray(prev) ? prev.map((n) => (n.id === id ? { ...n, read: true } : n)) : []
    );
  };

  const unreadCount = Array.isArray(notifications) ? notifications.filter((n) => !n.read).length : 0;

  return (
    <WebAppContext.Provider
      value={{
        activeSection,
        setActiveSection,
        health,
        pendingApprovals,
        notifications,
        unreadCount,
        isCommandPaletteOpen,
        setIsCommandPaletteOpen,
        isNotificationDrawerOpen,
        setIsNotificationDrawerOpen,
        preferences,
        updatePreferences,
        handleApprovalResponse,
        markNotificationRead,
        refreshHealth,
      }}
    >
      {children}
    </WebAppContext.Provider>
  );
};

export const useWebApp = () => {
  const context = useContext(WebAppContext);
  if (!context) {
    throw new Error('useWebApp must be used within a WebAppProvider');
  }
  return context;
};
