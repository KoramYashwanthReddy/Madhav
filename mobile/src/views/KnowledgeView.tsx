import React, { useState, useEffect } from 'react';
import { KnowledgeNode } from '../types';
import { mobileApiClient } from '../api/client';
import { BookOpen, Network } from 'lucide-react';

export const KnowledgeView: React.FC = () => {
  const [nodes, setNodes] = useState<KnowledgeNode[]>([]);

  useEffect(() => {
    mobileApiClient.getKnowledgeNodes().then(setNodes);
  }, []);

  return (
    <div className="mobile-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Personal Knowledge Graph
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 09 RAG Entity Provenance</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        {nodes.map((n) => (
          <div key={n.id} className="glass-card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '9px', textTransform: 'uppercase', color: 'var(--accent-cyan)', fontWeight: 700 }}>{n.node_type}</span>
            <h5 style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{n.label}</h5>
          </div>
        ))}
      </div>
    </div>
  );
};
