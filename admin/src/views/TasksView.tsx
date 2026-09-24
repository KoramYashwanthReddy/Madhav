import React, { useState, useEffect } from 'react';
import { TaskItem } from '../types';
import { adminApiClient } from '../api/admin/client';
import { CheckSquare } from 'lucide-react';

export const TasksView: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);

  useEffect(() => {
    adminApiClient.getTasks().then(setTasks);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Task Engine Operational Monitor
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 12 Task Engine & Multi-Agent Execution State</span>
      </div>

      <div className="admin-panel" style={{ padding: '16px', overflowX: 'auto' }}>
        <table className="admin-table">
          <thead>
            <tr>
              <th>Task ID</th>
              <th>Title</th>
              <th>Priority</th>
              <th>Assigned Agent</th>
              <th>Progress</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{t.id}</td>
                <td>{t.title}</td>
                <td style={{ textTransform: 'uppercase', fontSize: '10px', fontWeight: 700 }}>{t.priority}</td>
                <td>{t.assigned_agent || 'Unassigned'}</td>
                <td>{t.progress_percentage}%</td>
                <td>
                  <span className="admin-status-badge">
                    <span className={`status-dot ${t.status === 'in_progress' ? 'healthy' : ''}`} />
                    <span>{t.status.toUpperCase()}</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
