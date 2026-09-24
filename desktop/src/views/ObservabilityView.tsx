import React, { useEffect, useState } from "react";
import { Activity, ShieldCheck, Layers, RefreshCw } from "lucide-react";
import { api } from "../api/client";
import { AuditRecord, TraceSummary } from "../types";

export const ObservabilityView: React.FC = () => {
  const [traces, setTraces] = useState<TraceSummary[]>([]);
  const [audits, setAudits] = useState<AuditRecord[]>([]);
  const [activeTab, setActiveTab] = useState<"traces" | "audit" | "metrics">("traces");

  const loadData = async () => {
    const t = await api.getTraces();
    const a = await api.getAuditLogs();
    setTraces(t);
    setAudits(a);
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">Observability & Audit Dashboard</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            Real-time execution traces, OpenTelemetry spans, metrics, and append-only audit events (Module 33)
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadData}>
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tab Selectors */}
      <div style={{ display: "flex", gap: 10, borderBottom: "1px solid var(--border-color)", paddingBottom: 10 }}>
        <button
          className={`btn ${activeTab === "traces" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setActiveTab("traces")}
        >
          <Activity size={14} />
          <span>Execution Traces ({traces.length})</span>
        </button>
        <button
          className={`btn ${activeTab === "audit" ? "btn-primary" : "btn-secondary"}`}
          onClick={() => setActiveTab("audit")}
        >
          <ShieldCheck size={14} />
          <span>Append-Only Audit Log ({audits.length})</span>
        </button>
      </div>

      {/* Traces Tab */}
      {activeTab === "traces" && (
        <div className="card">
          <div className="card-title">
            <Layers size={18} style={{ color: "var(--accent-indigo)" }} />
            <span>OpenTelemetry Traces & Span Hierarchy</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {traces.map((tr) => (
              <div
                key={tr.trace_id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: 12,
                  borderRadius: 8,
                  background: "var(--bg-primary)",
                  border: "1px solid var(--border-color)",
                }}
              >
                <div>
                  <div style={{ fontFamily: "var(--font-family-mono)", fontSize: 13, fontWeight: 600 }}>
                    {tr.trace_id}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                    Spans: {tr.span_count} | Errors: {tr.error_count}
                  </div>
                </div>

                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 13, color: "#a5b4fc", fontWeight: 600 }}>
                    {tr.duration_ms} ms
                  </div>
                  <span className="status-pill online" style={{ fontSize: 10, padding: "2px 6px" }}>
                    {tr.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Audit Log Tab */}
      {activeTab === "audit" && (
        <div className="card">
          <div className="card-title">
            <ShieldCheck size={18} style={{ color: "var(--status-success)" }} />
            <span>Append-Only Immutable Audit Log</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {audits.map((aud) => (
              <div
                key={aud.event_id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: 12,
                  borderRadius: 8,
                  background: "var(--bg-primary)",
                  border: "1px solid var(--border-color)",
                }}
              >
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>
                    [{aud.event_type}] {aud.action} on {aud.target}
                  </div>
                  <div style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 2 }}>
                    Actor: {aud.actor} | Severity: {aud.severity} | {aud.timestamp}
                  </div>
                </div>

                <span
                  className={`status-pill ${aud.outcome === "ALLOWED" || aud.outcome === "SUCCESS" ? "online" : "offline"}`}
                  style={{ fontSize: 11 }}
                >
                  {aud.outcome}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
