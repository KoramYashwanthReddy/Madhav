import React from "react";
import { Shield, Server, Cpu } from "lucide-react";
import { useApp } from "../context/AppContext";

export const SettingsView: React.FC = () => {
  const { autonomyLevel, setAutonomyLevel, backendStatus, systemInfo } = useApp();

  const autonomyLabels = [
    "Level 0 — Observe Only (No notifications or actions)",
    "Level 1 — Notify & Ask (Default: Request explicit user authorization)",
    "Level 2 — Recommend & Propose (Suggest candidate actions for review)",
    "Level 3 — Autonomous Task Execution (Execute read-only / safe tasks)",
    "Level 4 — Autonomous Action Operator (Execute permitted actions automatically)",
    "Level 5 — Full Autonomous Workflow (Execute end-to-end multi-agent workflows)",
  ];

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">Settings & Autonomy Policy</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            Configure autonomy boundaries (Module 15 & 30), backend endpoints, and hardware profiles
          </p>
        </div>
      </div>

      {/* Autonomy Boundary Slider */}
      <div className="card">
        <div className="card-title">
          <Shield size={18} style={{ color: "var(--accent-purple)" }} />
          <span>Autonomy Operating Boundary (Module 15 & 30)</span>
        </div>

        <div style={{ marginBottom: 16 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8, fontSize: 14 }}>
            <span style={{ fontWeight: 600 }}>Active Autonomy Mode:</span>
            <span style={{ color: "#a78bfa", fontWeight: 700 }}>Level {autonomyLevel}</span>
          </div>

          <input
            type="range"
            min="0"
            max="5"
            step="1"
            value={autonomyLevel}
            onChange={(e) => setAutonomyLevel(parseInt(e.target.value, 10))}
            style={{ width: "100%", accentColor: "var(--accent-indigo)", cursor: "pointer" }}
          />

          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              background: "var(--bg-primary)",
              fontSize: 13,
              color: "var(--text-secondary)",
              border: "1px solid var(--border-color)",
            }}
          >
            {autonomyLabels[autonomyLevel]}
          </div>
        </div>
      </div>

      {/* Backend Connection Settings */}
      <div className="card">
        <div className="card-title">
          <Server size={18} style={{ color: "var(--accent-indigo)" }} />
          <span>Max Python Backend Connection</span>
        </div>

        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <div style={{ flex: 1 }}>
            <label style={{ display: "block", fontSize: 12, color: "var(--text-muted)", marginBottom: 4 }}>
              FastAPI Endpoint URL:
            </label>
            <input
              type="text"
              className="input-box"
              value={backendStatus.endpoint}
              readOnly
            />
          </div>
          <button className="btn btn-secondary" style={{ marginTop: 18 }}>
            <span>Test Ping</span>
          </button>
        </div>
      </div>

      {/* System Hardware Profile */}
      {systemInfo && (
        <div className="card">
          <div className="card-title">
            <Cpu size={18} style={{ color: "var(--accent-cyan)" }} />
            <span>Host Desktop System Information</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12, fontSize: 13 }}>
            <div style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 8 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 11 }}>OS / HOST</div>
              <div style={{ fontWeight: 600, marginTop: 4 }}>{systemInfo.os_name} ({systemInfo.host_name})</div>
            </div>
            <div style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 8 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 11 }}>CPU CORES</div>
              <div style={{ fontWeight: 600, marginTop: 4 }}>{systemInfo.cpu_count} Threads</div>
            </div>
            <div style={{ background: "var(--bg-primary)", padding: 12, borderRadius: 8 }}>
              <div style={{ color: "var(--text-muted)", fontSize: 11 }}>RAM USAGE</div>
              <div style={{ fontWeight: 600, marginTop: 4 }}>
                {systemInfo.used_memory_mb} / {systemInfo.total_memory_mb} MB
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
