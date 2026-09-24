import React, { useState, useEffect } from 'react';
import { KnowledgeGraphNode, KnowledgeGraphEdge } from '../types';
import { webApiClient } from '../api/client';
import { BookOpen, Network, FileText, Database } from 'lucide-react';

export const KnowledgeView: React.FC = () => {
  const [nodes, setNodes] = useState<KnowledgeGraphNode[]>([]);
  const [edges, setEdges] = useState<KnowledgeGraphEdge[]>([]);

  useEffect(() => {
    webApiClient.getKnowledgeGraph().then((data) => {
      setNodes(data.nodes);
      setEdges(data.edges);
    });
  }, []);

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          Personal Knowledge & RAG Graph
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 09 Personal Knowledge & Module 10 RAG Retrieval Engine
        </p>
      </div>

      {/* Graph Visualizer Placeholder / Summary */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Network size={20} style={{ color: 'var(--primary)' }} />
          <h3 style={{ fontSize: '15px', fontWeight: 600, margin: 0 }}>Knowledge Graph Entity Network</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '12px' }}>
          {nodes.map((n) => (
            <div key={n.id} className="glass-card" style={{ padding: '14px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--accent-cyan)', fontWeight: 700 }}>{n.node_type}</span>
                <Database size={14} style={{ color: 'var(--text-dim)' }} />
              </div>
              <h5 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{n.label}</h5>
            </div>
          ))}
        </div>

        <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)', marginTop: '8px', margin: 0 }}>Entity Graph Relationships</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {edges.map((e) => (
            <div key={e.id} style={{ fontSize: '12px', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', padding: '8px 12px', borderRadius: 'var(--radius-sm)', fontFamily: 'var(--font-mono)' }}>
              Node ({e.source_id}) --- [{e.relation}] ---&gt; Node ({e.target_id})
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
