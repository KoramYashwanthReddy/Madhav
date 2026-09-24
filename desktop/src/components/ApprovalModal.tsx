import React from "react";
import { ShieldAlert, Check, X, Clock } from "lucide-react";
import { useApp } from "../context/AppContext";

export const ApprovalModal: React.FC = () => {
  const { activeApprovals, approveSecurityRequest, denySecurityRequest } = useApp();

  if (activeApprovals.length === 0) return null;

  const current = activeApprovals[0];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 999,
      }}
    >
      <div
        className="card"
        style={{
          width: 520,
          borderColor: "var(--status-error)",
          boxShadow: "0 0 30px rgba(239, 68, 68, 0.3)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--status-error)", marginBottom: 12 }}>
          <ShieldAlert size={24} />
          <h3 style={{ fontSize: 18, fontWeight: 700 }}>Security Authorization Required (Module 15)</h3>
        </div>

        <p style={{ color: "var(--text-secondary)", fontSize: 14, marginBottom: 16 }}>
          An automated agent run or tool execution requires your explicit approval:
        </p>

        <div
          style={{
            background: "var(--bg-primary)",
            padding: 14,
            borderRadius: 8,
            border: "1px solid var(--border-color)",
            marginBottom: 16,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontWeight: 600, color: "var(--text-primary)" }}>Tool: {current.tool_name}</span>
            <span
              className="status-pill offline"
              style={{ padding: "2px 8px", fontSize: 11, fontWeight: 700 }}
            >
              Risk: {current.risk_level}
            </span>
          </div>
          <div style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 4 }}>
            <strong>Action:</strong> {current.action}
          </div>
          <div style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 4 }}>
            <strong>Target:</strong> {current.resource}
          </div>
          <div style={{ fontSize: 12, color: "#f59e0b", display: "flex", alignItems: "center", gap: 4, marginTop: 8 }}>
            <Clock size={12} />
            <span>Reason: {current.reason}</span>
          </div>
        </div>

        <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
          <button className="btn btn-danger" onClick={() => denySecurityRequest(current.id)}>
            <X size={16} />
            <span>DENY ACCESS</span>
          </button>
          <button className="btn btn-primary" onClick={() => approveSecurityRequest(current.id)}>
            <Check size={16} />
            <span>AUTHORIZE & ALLOW</span>
          </button>
        </div>
      </div>
    </div>
  );
};
