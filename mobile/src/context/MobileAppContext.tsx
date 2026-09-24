import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  BottomTab,
  MobileView,
  ConnectionMode,
  DeviceInfo,
  BackendHealth,
  SecurityApprovalRequest,
  ProactiveNotification,
} from '../types';
import { mobileApiClient } from '../api/client';
import { deviceCapabilityService } from '../services/DeviceCapabilityService';
import { mobileAgentService } from '../services/MobileAgentService';
import { voiceService } from '../services/VoiceService';

interface MobileAppContextType {
  activeTab: BottomTab;
  setActiveTab: (tab: BottomTab) => void;
  activeMoreView: MobileView;
  setActiveMoreView: (view: MobileView) => void;
  currentView: MobileView;
  connectionMode: ConnectionMode;
  setConnectionMode: (mode: ConnectionMode) => void;
  health: BackendHealth | null;
  deviceInfo: DeviceInfo | null;
  pendingApprovals: SecurityApprovalRequest[];
  notifications: ProactiveNotification[];
  unreadCount: number;
  isEmergencyStopped: boolean;
  triggerEmergencyStop: () => void;
  resetEmergencyStop: () => void;
  isBiometricLocked: boolean;
  unlockBiometrics: () => void;
  autonomyLevel: number; // 0 - 5
  setAutonomyLevel: (level: number) => void;
  isMoreDrawerOpen: boolean;
  setIsMoreDrawerOpen: (open: boolean) => void;
  handleApprovalResponse: (id: string, approved: boolean) => Promise<void>;
  markNotificationRead: (id: string) => void;
}

const MobileAppContext = createContext<MobileAppContextType | undefined>(undefined);

export const MobileAppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeTab, setActiveTab] = useState<BottomTab>('home');
  const [activeMoreView, setActiveMoreView] = useState<MobileView>('memory');
  const [connectionMode, setConnectionMode] = useState<ConnectionMode>('LOCAL');
  const [health, setHealth] = useState<BackendHealth | null>(null);
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo | null>(null);
  const [pendingApprovals, setPendingApprovals] = useState<SecurityApprovalRequest[]>([]);
  const [notifications, setNotifications] = useState<ProactiveNotification[]>([]);
  const [isEmergencyStopped, setIsEmergencyStopped] = useState(false);
  const [isBiometricLocked, setIsBiometricLocked] = useState(false);
  const [autonomyLevel, setAutonomyLevel] = useState<number>(2); // Level 2 - Guarded
  const [isMoreDrawerOpen, setIsMoreDrawerOpen] = useState(false);

  const currentView: MobileView = activeTab === 'more' ? activeMoreView : (activeTab as MobileView);

  const refreshHealth = async () => {
    try {
      const h = await mobileApiClient.getHealth();
      setHealth(h);
      if (h.status === 'ok') setConnectionMode('LOCAL');
    } catch {
      setHealth(null);
      setConnectionMode('OFFLINE');
    }
  };

  const loadInitialData = async () => {
    await refreshHealth();
    try {
      const d = await deviceCapabilityService.getDeviceStatus();
      setDeviceInfo(d);
      await mobileApiClient.registerDevice(d);

      const apps = await mobileApiClient.getPendingApprovals();
      setPendingApprovals(apps);
      const notifs = await mobileApiClient.getNotifications();
      setNotifications(notifs);
    } catch {
      // API fallback
    }
  };

  useEffect(() => {
    loadInitialData();
    const interval = setInterval(refreshHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const triggerEmergencyStop = () => {
    mobileAgentService.triggerEmergencyStop();
    voiceService.stopListening();
    setIsEmergencyStopped(true);
  };

  const resetEmergencyStop = () => {
    mobileAgentService.resetEmergencyStop();
    setIsEmergencyStopped(false);
  };

  const unlockBiometrics = () => {
    setIsBiometricLocked(false);
  };

  const handleApprovalResponse = async (id: string, approved: boolean) => {
    await mobileApiClient.respondApproval(id, approved);
    setPendingApprovals((prev) => prev.filter((a) => a.id !== id));
  };

  const markNotificationRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    );
  };

  const unreadCount = notifications.filter((n) => !n.read).length;

  return (
    <MobileAppContext.Provider
      value={{
        activeTab,
        setActiveTab,
        activeMoreView,
        setActiveMoreView,
        currentView,
        connectionMode,
        setConnectionMode,
        health,
        deviceInfo,
        pendingApprovals,
        notifications,
        unreadCount,
        isEmergencyStopped,
        triggerEmergencyStop,
        resetEmergencyStop,
        isBiometricLocked,
        unlockBiometrics,
        autonomyLevel,
        setAutonomyLevel,
        isMoreDrawerOpen,
        setIsMoreDrawerOpen,
        handleApprovalResponse,
        markNotificationRead,
      }}
    >
      {children}
    </MobileAppContext.Provider>
  );
};

export const useMobileApp = () => {
  const context = useContext(MobileAppContext);
  if (!context) {
    throw new Error('useMobileApp must be used within a MobileAppProvider');
  }
  return context;
};
