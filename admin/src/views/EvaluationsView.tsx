import React, { useState, useEffect } from 'react';
import { EvaluationMetric } from '../types';
import { adminApiClient } from '../api/admin/client';
import { Award } from 'lucide-react';

export const EvaluationsView: React.FC = () => {
  const [evals, setEvals] = useState<EvaluationMetric[]>([]);

  useEffect(() => {
    adminApiClient.getEvaluations().then(setEvals);
  }, []);

  return (
    <div className="admin-view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '18px', fontWeight: 700, margin: 0 }}>
          Evaluation Datasets & Benchmarks
        </h2>
        <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Module 32 Quality & Safety Evaluation Benchmarks</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px' }}>
        {evals.map((ev) => (
          <div key={ev.id} className="admin-card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{ev.run_name}</h4>
              <Award size={16} style={{ color: 'var(--primary)' }} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px' }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Faithfulness</span>
                <strong style={{ display: 'block', color: 'var(--status-healthy)', fontSize: '15px' }}>{(ev.faithfulness_score * 100).toFixed(0)}%</strong>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '8px', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ color: 'var(--text-muted)' }}>Tool Precision</span>
                <strong style={{ display: 'block', color: 'var(--accent-purple)', fontSize: '15px' }}>{(ev.tool_precision * 100).toFixed(0)}%</strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
