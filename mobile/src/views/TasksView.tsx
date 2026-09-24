import React, { useState, useEffect } from 'react';
import { TaskItem } from '../types';
import { mobileApiClient } from '../api/client';
import { CheckSquare, Plus, Bot, Clock } from 'lucide-react';

export const TasksView: React.FC = () => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [title, setTitle] = useState('');
  const [desc, setDesc] = useState('');

  useEffect(() => {
    mobileApiClient.getTasks().then(setTasks);
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    const newTask = await mobileApiClient.createTask(title, desc);
    setTasks((prev) => [newTask, ...prev]);
    setTitle('');
    setDesc('');
    setIsCreating(false);
  };

  return (
    <div className="mobile-view-container">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
            Task Engine
          </h2>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 12 Tasks & Agent Delegation</span>
        </div>
        <button onClick={() => setIsCreating(true)} className="btn btn-primary" style={{ minHeight: '36px', padding: '6px 12px', fontSize: '12px' }}>
          <Plus size={14} />
          <span>New</span>
        </button>
      </div>

      {isCreating && (
        <form onSubmit={handleCreate} className="glass-panel" style={{ padding: '14px', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: 600, margin: 0 }}>Create Task Prompt</h4>
          <input
            type="text"
            placeholder="Task Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input-field"
            required
          />
          <textarea
            placeholder="Task instructions..."
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            className="input-field"
            rows={2}
          />
          <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={() => setIsCreating(false)} className="btn btn-secondary" style={{ minHeight: '34px', padding: '4px 10px', fontSize: '12px' }}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" style={{ minHeight: '34px', padding: '4px 12px', fontSize: '12px' }}>
              Create
            </button>
          </div>
        </form>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {tasks.map((t) => (
          <div key={t.id} className="glass-card" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckSquare size={16} style={{ color: 'var(--primary)' }} />
                <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{t.title}</h4>
              </div>
              <span className="status-badge" style={{ fontSize: '10px' }}>
                {t.status}
              </span>
            </div>

            <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: 0 }}>{t.description}</p>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-dim)' }}>
              <span>{t.assigned_agent || 'Mobile Agent'}</span>
              <span>{t.progress_percentage}% Completed</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
