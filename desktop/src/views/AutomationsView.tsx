import React, { useState } from "react";
import { Calendar, Play, Pause, Sparkles } from "lucide-react";
import { AutomationJob } from "../types";

export const AutomationsView: React.FC = () => {
  const [jobs, setJobs] = useState<AutomationJob[]>([
    {
      id: "job-1",
      name: "Daily Developer Repository Summary",
      cron_expression: "0 9 * * *",
      status: "active",
      last_run: "Today, 09:00",
      next_run: "Tomorrow, 09:00",
    },
    {
      id: "job-2",
      name: "System Telemetry & Audit Maintenance",
      cron_expression: "0 0 * * 0",
      status: "active",
      last_run: "Sunday, 00:00",
      next_run: "Next Sunday, 00:00",
    },
  ]);

  const toggleJob = (id: string) => {
    setJobs((prev) =>
      prev.map((j) => (j.id === id ? { ...j, status: j.status === "active" ? "paused" : "active" } : j))
    );
  };

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">Automations & Scheduler</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            Manage background cron tasks, proactive intelligence candidates, and triggers (Modules 28 & 30)
          </p>
        </div>
      </div>

      {/* Proactive Intelligence Candidate Notification Alert */}
      <div
        className="card"
        style={{
          borderColor: "rgba(139, 92, 246, 0.4)",
          background: "linear-gradient(135deg, rgba(31, 41, 55, 0.8) 0%, rgba(139, 92, 246, 0.1) 100%)",
        }}
      >
        <div className="card-title" style={{ color: "#a78bfa" }}>
          <Sparkles size={18} />
          <span>Proactive Intelligence Candidate (Module 30)</span>
        </div>
        <p style={{ fontSize: 14, color: "var(--text-primary)", marginBottom: 8 }}>
          Max detected repeated build verification requests after code edits. Would you like to schedule an automated post-commit build trigger?
        </p>
        <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
          <button className="btn btn-primary">
            <span>Accept Recommendation</span>
          </button>
          <button className="btn btn-secondary">
            <span>Dismiss</span>
          </button>
        </div>
      </div>

      {/* Scheduled Automation Jobs */}
      <div className="card">
        <div className="card-title">
          <Calendar size={18} style={{ color: "var(--accent-indigo)" }} />
          <span>Configured Background Jobs (Module 28)</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {jobs.map((job) => (
            <div
              key={job.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: 14,
                borderRadius: 8,
                background: "var(--bg-primary)",
                border: "1px solid var(--border-color)",
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{job.name}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  Cron: <code>{job.cron_expression}</code> | Last: {job.last_run} | Next: {job.next_run}
                </div>
              </div>

              <button
                className={`btn ${job.status === "active" ? "btn-secondary" : "btn-primary"}`}
                onClick={() => toggleJob(job.id)}
              >
                {job.status === "active" ? <Pause size={14} /> : <Play size={14} />}
                <span>{job.status === "active" ? "Pause" : "Resume"}</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
