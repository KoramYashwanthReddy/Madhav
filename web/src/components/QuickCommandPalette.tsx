import React, { useState } from 'react';
import { useWebApp } from '../context/WebAppContext';
import { NavSection } from '../types';
import { Search, X, Command, MessageSquare, CheckSquare, Brain, Bot, Wrench, Settings, LucideIcon } from 'lucide-react';

export const QuickCommandPalette: React.FC = () => {
  const { isCommandPaletteOpen, setIsCommandPaletteOpen, setActiveSection } = useWebApp();
  const [query, setQuery] = useState('');

  if (!isCommandPaletteOpen) return null;

  const quickLinks: Array<{ label: string; section: NavSection; category: string; icon: LucideIcon }> = [
    { label: 'Go to Conversational Chat', section: 'chat', category: 'Navigation', icon: MessageSquare },
    { label: 'View Active Tasks & Workflows', section: 'tasks', category: 'Navigation', icon: CheckSquare },
    { label: 'Inspect Memory & Fact Graph', section: 'memory', category: 'Navigation', icon: Brain },
    { label: 'Manage AI Agents', section: 'agents', category: 'Navigation', icon: Bot },
    { label: 'Explore Tool Registry Sandbox', section: 'tools', category: 'Navigation', icon: Wrench },
    { label: 'Configure System Settings & Autonomy', section: 'settings', category: 'Navigation', icon: Settings },
  ];

  const filteredLinks = quickLinks.filter((link) =>
    link.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (section: NavSection) => {
    setActiveSection(section);
    setIsCommandPaletteOpen(false);
    setQuery('');
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '100px',
      }}
      onClick={() => setIsCommandPaletteOpen(false)}
    >
      <div
        className="glass-panel"
        style={{
          width: '560px',
          maxWidth: '90vw',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Input Bar */}
        <div style={{ display: 'flex', alignItems: 'center', padding: '16px 20px', borderBottom: '1px solid var(--border-glass)', gap: '12px' }}>
          <Search size={20} style={{ color: 'var(--primary)' }} />
          <input
            type="text"
            placeholder="Type a command, query memory, or jump to section..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-main)',
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
            }}
          />
          <button
            onClick={() => setIsCommandPaletteOpen(false)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Results List */}
        <div style={{ maxHeight: '360px', overflowY: 'auto', padding: '12px' }}>
          {filteredLinks.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
              No matching commands or navigation sections found for "{query}".
            </div>
          ) : (
            filteredLinks.map((item, idx) => {
              const IconComp = item.icon;
              return (
                <div
                  key={idx}
                  onClick={() => handleSelect(item.section)}
                  className="glass-card"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '14px',
                    padding: '12px 16px',
                    marginBottom: '6px',
                    cursor: 'pointer',
                    borderRadius: 'var(--radius-md)',
                  }}
                >
                  <IconComp size={18} style={{ color: 'var(--primary)' }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text-main)' }}>{item.label}</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{item.category}</div>
                  </div>
                  <kbd style={{ fontSize: '11px', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '4px' }}>
                    Jump
                  </kbd>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '10px 16px', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-dim)' }}>
          <span>Navigation Quick Launcher</span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Command size={12} /> + K to toggle
          </span>
        </div>
      </div>
    </div>
  );
};
