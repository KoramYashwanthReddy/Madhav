import React, { useState, useEffect } from 'react';
import { TaskItem } from '../types';
import { webApiClient } from '../api/client';
import { CheckSquare, Plus, Bot, Clock, AlertCircle, CheckCircle2 } from 'lucide-react';

export const TasksView: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [newTitle, setNewTitle] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    webApiClient.getTasks().then(setTasks);
  }, []);

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    const task = await webApiClient.createTask(newTitle, newDesc);
    setTasks((prev) => [task, ...prev]);
    setNewTitle('');
    setNewDesc('');
    setIsCreating(false);
  };

  return (
    <div className="view-container">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
            Task Engine & Multi-Agent Workflows
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
            Module 12 Task Engine & Module 13 Agent Delegation
          </p>
        </div>
        <button
          onClick={() => setIsCreating(true)}
          className="btn btn-primary"
        >
          <Plus size={16} />
          <span>New Task</span>
        </button>
      </div>

      {/* Creation Modal / Form */}
      {isCreating && (
        <form onSubmit={handleCreateTask} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: 600, margin: 0 }}>Create Autonomous Goal Task</h3>
          <input
            type="text"
            placeholder="Task Title (e.g. Audit security dependencies)"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            className="input-field"
            required
          />
          <textarea
            placeholder="Detailed task prompt instructions..."
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            className="input-field"
            rows={3}
          />
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={() => setIsCreating(false)} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Launch Task
            </button>
          </div>
        </form>
      )}

      {/* Task Cards List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {tasks.map((t) => (
          <div key={t.id} className="glass-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <CheckSquare size={18} style={{ color: 'var(--primary)' }} />
                <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{t.title}</h4>
              </div>
              <span
                className="status-badge"
                style={{
                  background:
                    t.status === 'running'
                      ? 'rgba(99, 102, 241, 0.2)'
                      : t.status === 'completed'
                      ? 'rgba(34, 197, 94, 0.2)'
                      : 'rgba(255, 255, 255, 0.05)',
                  color: t.status === 'running' ? 'var(--primary)' : t.status === 'completed' ? 'var(--status-online)' : 'var(--text-muted)',
                }}
              >
                {t.status.toUpperCase()}
              </span>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0 }}>{t.description}</p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-dim)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Bot size={14} />
                <span>{t.assigned_agent || 'Unassigned'}</span>
              </div>
              <span>Progress: {t.steps_completed} / {t.steps_total} Steps ({t.progress_percentage}%)</span>
            </div>

            {/* Progress Bar */}
            <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '999px', overflow: 'hidden' }}>
              <div
                style={{
                  width: `${t.progress_percentage}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, var(--primary) 0%, var(--accent-cyan) 100%)',
                  borderRadius: '999px',
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
