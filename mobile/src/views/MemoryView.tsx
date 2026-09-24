import React, { useState, useEffect } from 'react';
import { MemoryEntry } from '../types';
import { mobileApiClient } from '../api/client';
import { Brain, Tag } from 'lucide-react';

export const MemoryView: React.FC = () => {
  const [memories, setMemories] = useState<MemoryEntry[]>([]);

  useEffect(() => {
    mobileApiClient.getMemories().then(setMemories);
  }, []);

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Memory Engine
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 08 Stored User Preferences & Facts</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
        {memories.map((m) => (
          <div key={m.id} className="glass-card" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--accent-purple)', fontWeight: 700 }}>
                {m.memory_type}
              </span>
              <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
                Importance: {(m.importance * 100).toFixed(0)}%
              </span>
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-main)', margin: 0 }}>{m.content}</p>

            <div style={{ display: 'flex', gap: '4px' }}>
              {m.tags.map((t, idx) => (
                <span key={idx} style={{ fontSize: '10px', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px' }}>
                  #{t}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
