import React, { useState } from "react";
import { Share2, Github, Globe, Terminal, Folder, CheckCircle } from "lucide-react";
import { IntegrationConn } from "../types";

export const IntegrationsView: React.FC = () => {
  const [integrations] = useState<IntegrationConn[]>([
    {
      id: "int-1",
      name: "GitHub Developer Integration",
      provider: "github",
      status: "connected",
      last_sync: "10 mins ago",
    },
    {
      id: "int-2",
      name: "Web Intelligence Agent",
      provider: "web",
      status: "connected",
      last_sync: "Just now",
    },
    {
      id: "int-3",
      name: "Filesystem Agent Bridge",
      provider: "filesystem",
      status: "connected",
      last_sync: "Active",
    },
    {
      id: "int-4",
      name: "Terminal Control Agent",
      provider: "terminal",
      status: "connected",
      last_sync: "Active",
    },
  ]);

  const getIcon = (provider: string) => {
    switch (provider) {
      case "github":
        return <Github size={20} />;
      case "web":
        return <Globe size={20} />;
      case "filesystem":
        return <Folder size={20} />;
      case "terminal":
        return <Terminal size={20} />;
      default:
        return <Share2 size={20} />;
    }
  };

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">External Integrations & Connectors</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            Manage external APIs, GitHub repositories, and system agent bridges (Module 29)
          </p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        {integrations.map((item) => (
          <div key={item.id} className="card">
            <div className="card-title">
              {getIcon(item.provider)}
              <span>{item.name}</span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13, color: "var(--status-success)" }}>
                <CheckCircle size={14} />
                <span>Status: Connected</span>
              </div>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>Last Sync: {item.last_sync}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
