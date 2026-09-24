import React, { useEffect, useState } from "react";
import { RefreshCw, Cpu, Layers } from "lucide-react";
import { api } from "../api/client";
import { AgentRun, TaskItem } from "../types";

export const TasksView: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [agents] = useState<AgentRun[]>([
    {
      id: "agent-1",
      agent_name: "Coding & Developer Agent",
      agent_type: "Module 22",
      status: "executing",
      current_step: "Running static type checker and unit test suite",
      duration_ms: 1240,
    },
    {
      id: "agent-2",
      agent_name: "Web Intelligence Agent",
      agent_type: "Module 21",
      status: "idle",
      current_step: "Awaiting search query delegation",
      duration_ms: 0,
    },
  ]);

  const loadTasks = async () => {
    const list = await api.getTasks();
    setTasks(list);
  };

  useEffect(() => {
    loadTasks();
  }, []);

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">Task & Agent Workspace</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            Monitor and delegate autonomous task execution graphs (Modules 12 & 13)
          </p>
        </div>
        <button className="btn btn-secondary" onClick={loadTasks}>
          <RefreshCw size={14} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Active Agents Summary Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
        {agents.map((ag) => (
          <div key={ag.id} className="card">
            <div className="card-title">
              <Cpu size={18} style={{ color: "var(--accent-purple)" }} />
              <span>{ag.agent_name}</span>
              <span
                className={`status-pill ${ag.status === "executing" ? "online" : ""}`}
                style={{ marginLeft: "auto", fontSize: 11 }}
              >
                {ag.status.toUpperCase()}
              </span>
            </div>
            <p style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 8 }}>
              <strong>Module:</strong> {ag.agent_type}
            </p>
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>
              <strong>Current Step:</strong> {ag.current_step}
            </p>
          </div>
        ))}
      </div>

      {/* Task List Card */}
      <div className="card">
        <div className="card-title">
          <Layers size={18} style={{ color: "var(--accent-indigo)" }} />
          <span>Active Task Execution Queue</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {tasks.map((task) => (
            <div
              key={task.id}
              style={{
                background: "var(--bg-primary)",
                padding: 14,
                borderRadius: 8,
                border: "1px solid var(--border-color)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <span style={{ fontWeight: 600, fontSize: 14 }}>{task.title}</span>
                <span className={`status-pill ${task.status === "completed" ? "online" : ""}`} style={{ fontSize: 11 }}>
                  {task.status.toUpperCase()} ({task.progress}%)
                </span>
              </div>

              {/* Subtasks */}
              {task.subtasks && (
                <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
                  {task.subtasks.map((st) => (
                    <span
                      key={st}
                      style={{
                        fontSize: 11,
                        background: "var(--bg-surface-hover)",
                        padding: "2px 8px",
                        borderRadius: 4,
                        color: "var(--text-secondary)",
                      }}
                    >
                      ✓ {st}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
