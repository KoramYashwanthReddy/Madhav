import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  AdminSection,
  AdminRole,
  SecurityMode,
  ComponentHealth,
  SystemAlert,
} from '../types';
import { adminApiClient } from '../api/admin/client';

interface AdminContextType {
  activeSection: AdminSection;
  setActiveSection: (section: AdminSection) => void;
  adminRole: AdminRole;
  setAdminRole: (role: AdminRole) => void;
  securityMode: SecurityMode;
  setSecurityMode: (mode: SecurityMode) => void;
  isReadOnly: boolean;
  setIsReadOnly: (readOnly: boolean) => void;
  healthComponents: ComponentHealth[];
  alerts: SystemAlert[];
  isGlobalSearchOpen: boolean;
  setIsGlobalSearchOpen: (open: boolean) => void;
  isKillSwitchModalOpen: boolean;
  setIsKillSwitchModalOpen: (open: boolean) => void;
  dangerousActionModal: {
    isOpen: boolean;
    title: string;
    description: string;
    actionType: string;
    targetId: string;
    onConfirm: () => Promise<void>;
  } | null;
  openDangerousActionModal: (
    title: string,
    description: string,
    actionType: string,
    targetId: string,
    onConfirm: () => Promise<void>
  ) => void;
  closeDangerousActionModal: () => void;
  refreshHealth: () => Promise<void>;
  triggerKillSwitch: () => Promise<void>;
}

const AdminContext = createContext<AdminContextType | undefined>(undefined);

export const AdminProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeSection, setActiveSection] = useState<AdminSection>('dashboard');
  const [adminRole, setAdminRole] = useState<AdminRole>('SUPER_ADMIN');
  const [securityMode, setSecurityMode] = useState<SecurityMode>('NORMAL');
  const [isReadOnly, setIsReadOnly] = useState<boolean>(false);
  const [healthComponents, setHealthComponents] = useState<ComponentHealth[]>([]);
  const [alerts, setAlerts] = useState<SystemAlert[]>([]);
  const [isGlobalSearchOpen, setIsGlobalSearchOpen] = useState(false);
  const [isKillSwitchModalOpen, setIsKillSwitchModalOpen] = useState(false);
  const [dangerousActionModal, setDangerousActionModal] = useState<{
    isOpen: boolean;
    title: string;
    description: string;
    actionType: string;
    targetId: string;
    onConfirm: () => Promise<void>;
  } | null>(null);

  const refreshHealth = async () => {
    try {
      const components = await adminApiClient.getComponentHealth();
      setHealthComponents(components);
      const systemAlerts = await adminApiClient.getSystemAlerts();
      setAlerts(systemAlerts);
    } catch {
      // API fallback
    }
  };

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(refreshHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcut listener (Ctrl+K or Cmd+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsGlobalSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const openDangerousActionModal = (
    title: string,
    description: string,
    actionType: string,
    targetId: string,
    onConfirm: () => Promise<void>
  ) => {
    setDangerousActionModal({
      isOpen: true,
      title,
      description,
      actionType,
      targetId,
      onConfirm,
    });
  };

  const closeDangerousActionModal = () => {
    setDangerousActionModal(null);
  };

  const triggerKillSwitch = async () => {
    await adminApiClient.triggerKillSwitch();
    setSecurityMode('LOCKDOWN');
    setIsKillSwitchModalOpen(false);
    refreshHealth();
  };

  return (
    <AdminContext.Provider
      value={{
        activeSection,
        setActiveSection,
        adminRole,
        setAdminRole,
        securityMode,
        setSecurityMode,
        isReadOnly,
        setIsReadOnly,
        healthComponents,
        alerts,
        isGlobalSearchOpen,
        setIsGlobalSearchOpen,
        isKillSwitchModalOpen,
        setIsKillSwitchModalOpen,
        dangerousActionModal,
        openDangerousActionModal,
        closeDangerousActionModal,
        refreshHealth,
        triggerKillSwitch,
      }}
    >
      {children}
    </AdminContext.Provider>
  );
};

export const useAdmin = () => {
  const context = useContext(AdminContext);
  if (!context) {
    throw new Error('useAdmin must be used within an AdminProvider');
  }
  return context;
};
