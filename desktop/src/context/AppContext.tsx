import React, { createContext, useContext, useEffect, useState } from "react";
import {
  BackendStatus,
  SecurityApprovalRequest,
  SystemInfo,
  ViewType,
} from "../types";
import { checkBackendStatusNative, getSystemInfoNative } from "../api/tauri_bridge";

interface AppContextType {
  activeView: ViewType;
  setActiveView: (view: ViewType) => void;
  backendStatus: BackendStatus;
  systemInfo: SystemInfo | null;
  autonomyLevel: number;
  setAutonomyLevel: (level: number) => void;
  activeApprovals: SecurityApprovalRequest[];
  approveSecurityRequest: (id: string) => void;
  denySecurityRequest: (id: string) => void;
  notificationsCount: number;
  refreshBackendStatus: () => Promise<void>;
  isOverlayMode: boolean;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeView, setActiveView] = useState<ViewType>("chat");
  const [autonomyLevel, setAutonomyLevel] = useState<number>(1);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>({
    is_running: false,
    endpoint: "http://127.0.0.1:8000",
    latency_ms: 0,
    status_code: 0,
    message: "Connecting...",
  });
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [notificationsCount] = useState<number>(3);
  const [isOverlayMode] = useState<boolean>(
    typeof window !== "undefined" &&
      (window.location.hash === "#overlay" || window.location.search.includes("overlay=true"))
  );

  // Mock active Module 15 security approval request for demonstration & safety verification
  const [activeApprovals, setActiveApprovals] = useState<SecurityApprovalRequest[]>([
    {
      id: "appr-101",
      tool_name: "terminal_execute",
      action: "Run build & restart background service",
      resource: "terminal://cmd.exe",
      risk_level: "HIGH",
      reason: "Requires explicit user authorization under Autonomy Level 1",
      expires_at: new Date(Date.now() + 300000).toISOString(),
    },
  ]);

  const refreshBackendStatus = async () => {
    const status = await checkBackendStatusNative();
    setBackendStatus(status);
  };

  useEffect(() => {
    refreshBackendStatus();
    getSystemInfoNative().then(setSystemInfo);

    const interval = setInterval(refreshBackendStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const approveSecurityRequest = (id: string) => {
    setActiveApprovals((prev) => prev.filter((a) => a.id !== id));
  };

  const denySecurityRequest = (id: string) => {
    setActiveApprovals((prev) => prev.filter((a) => a.id !== id));
  };

  return (
    <AppContext.Provider
      value={{
        activeView,
        setActiveView,
        backendStatus,
        systemInfo,
        autonomyLevel,
        setAutonomyLevel,
        activeApprovals,
        approveSecurityRequest,
        denySecurityRequest,
        notificationsCount,
        refreshBackendStatus,
        isOverlayMode,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error("useApp must be used within an AppProvider");
  }
  return context;
};
