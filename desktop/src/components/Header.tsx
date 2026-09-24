import React from "react";
import { ShieldCheck, Zap, Bell, Command, User } from "lucide-react";
import { useApp } from "../context/AppContext";
import { toggleOverlayWindowNative } from "../api/tauri_bridge";

export const Header: React.FC = () => {
  const { backendStatus, autonomyLevel, notificationsCount } = useApp();

  const handleToggleOverlay = async () => {
    await toggleOverlayWindowNative();
  };

  return (
    <header className="header-bar">
      <div className="header-title">
        <Zap size={20} className="pulse" style={{ color: "#6366f1" }} />
        <span>MAX DESKTOP</span>
      </div>

      <div className="header-actions">
        {/* Connection Status Pill */}
        <div className={`status-pill ${backendStatus.is_running ? "online" : "offline"}`}>
          <div className="status-dot" />
          <span>
            {backendStatus.is_running
              ? `Backend Connected (${backendStatus.latency_ms}ms)`
              : "Backend Offline"}
          </span>
        </div>

        {/* Autonomy Level Pill */}
        <div className="status-pill online" style={{ borderColor: "rgba(139, 92, 246, 0.3)", color: "#a78bfa" }}>
          <ShieldCheck size={14} />
          <span>Autonomy L{autonomyLevel}</span>
        </div>

        {/* Quick HUD Overlay Button */}
        <button className="btn btn-secondary" onClick={handleToggleOverlay} title="Toggle Quick HUD (Alt+Space)">
          <Command size={14} />
          <span>HUD</span>
        </button>

        {/* Notification Bell */}
        <div style={{ position: "relative" }}>
          <button className="btn btn-secondary" style={{ padding: "8px" }}>
            <Bell size={16} />
          </button>
          {notificationsCount > 0 && (
            <span
              style={{
                position: "absolute",
                top: -4,
                right: -4,
                background: "#ec4899",
                color: "#ffffff",
                borderRadius: "50%",
                width: 16,
                height: 16,
                fontSize: 10,
                fontWeight: 700,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              {notificationsCount}
            </span>
          )}
        </div>

        {/* User Profile Avatar */}
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: "50%",
            background: "var(--gradient-primary)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#ffffff",
            fontWeight: 700,
            fontSize: 14,
          }}
        >
          <User size={16} />
        </div>
      </div>
    </header>
  );
};
