import React, { useState, useEffect } from 'react';
import { MemoryEntry } from '../types';
import { webApiClient } from '../api/client';
import { Brain, Search, Tag, Sparkles } from 'lucide-react';

export const MemoryView: React.FC = () => {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    webApiClient.getMemories(searchQuery).then(setMemories);
  }, [searchQuery]);

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          Memory Engine & User Preferences
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 08 Memory Engine & Module 31 Learning Engine
        </p>
      </div>

      {/* Search Input */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '12px', color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search stored facts, user preferences, and learned concepts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-field"
            style={{ paddingLeft: '38px' }}
          />
        </div>
      </div>

      {/* Memories Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '16px' }}>
        {memories.map((mem) => (
          <div key={mem.id} className="glass-card" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 600,
                  textTransform: 'uppercase',
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: 'rgba(168, 85, 247, 0.2)',
                  color: 'var(--accent-purple)',
                }}
              >
                {mem.memory_type}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                Importance: {(mem.importance * 100).toFixed(0)}%
              </span>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-main)', margin: 0, lineHeight: 1.5 }}>
              {mem.content}
            </p>

            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
              {mem.tags.map((tag, idx) => (
                <span
                  key={idx}
                  style={{
                    fontSize: '11px',
                    color: 'var(--text-muted)',
                    background: 'rgba(255,255,255,0.05)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <Tag size={10} />
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
