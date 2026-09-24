import React, { useState } from 'react';
import { useAdmin } from '../context/AdminContext';
import { AdminSection } from '../types';
import { Search, X, CheckSquare, Bot, Wrench, Smartphone, FileText, Database, LucideIcon } from 'lucide-react';

export const GlobalSearchModal: React.FC = () => {
  const { isGlobalSearchOpen, setIsGlobalSearchOpen, setActiveSection } = useAdmin();
  const [query, setQuery] = useState('');

  if (!isGlobalSearchOpen) return null;

  const quickJumpTargets: Array<{ label: string; section: AdminSection; type: string; icon: LucideIcon }> = [
    { label: 'Inspect AI Runtime Latencies & Request Throughput', section: 'runtime', type: 'Runtime', icon: Database },
    { label: 'View Multi-Agent Task Execution Status', section: 'tasks', type: 'Task', icon: CheckSquare },
    { label: 'Manage Module 14 Tool Sandbox Registry', section: 'tools', type: 'Tool', icon: Wrench },
    { label: 'Inspect Registered Devices & Client Sessions', section: 'devices', type: 'Device', icon: Smartphone },
    { label: 'Search Module 33 Audit Log Events', section: 'audit', type: 'Audit', icon: FileText },
    { label: 'Run Safe Predefined Diagnostics Suite', section: 'diagnostics', type: 'Diagnostic', icon: Bot },
  ];

  const filtered = quickJumpTargets.filter((item) =>
    item.label.toLowerCase().includes(query.toLowerCase())
  );

  const handleSelect = (section: AdminSection) => {
    setActiveSection(section);
    setIsGlobalSearchOpen(false);
    setQuery('');
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        backdropFilter: 'blur(8px)',
        zIndex: 9999,
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'center',
        paddingTop: '80px',
      }}
      onClick={() => setIsGlobalSearchOpen(false)}
    >
      <div
        className="admin-panel"
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
        <div style={{ display: 'flex', alignItems: 'center', padding: '14px 18px', borderBottom: '1px solid var(--border-color)', gap: '10px' }}>
          <Search size={18} style={{ color: 'var(--primary)' }} />
          <input
            type="text"
            placeholder="Search operational resources, audit logs, devices, tools..."
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
              fontSize: '13px',
            }}
          />
          <button
            onClick={() => setIsGlobalSearchOpen(false)}
            style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
          >
            <X size={18} />
          </button>
        </div>

        <div style={{ maxHeight: '340px', overflowY: 'auto', padding: '10px' }}>
          {filtered.length === 0 ? (
            <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '12px' }}>
              No operational resources matching "{query}".
            </div>
          ) : (
            filtered.map((item, idx) => {
              const IconComp = item.icon;
              return (
                <div
                  key={idx}
                  onClick={() => handleSelect(item.section)}
                  className="admin-card"
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '12px',
                    padding: '10px 14px',
                    marginBottom: '4px',
                    cursor: 'pointer',
                  }}
                >
                  <IconComp size={16} style={{ color: 'var(--primary)' }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)' }}>{item.label}</div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{item.type}</div>
                  </div>
                  <kbd style={{ fontSize: '10px', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '3px' }}>
                    Navigate
                  </kbd>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
};
