import React, { useState, useEffect } from 'react';
import { EvaluationMetric } from '../types';
import { webApiClient } from '../api/client';
import { Award, BarChart2, ShieldCheck, Zap } from 'lucide-react';

export const EvaluationsView: React.FC = () => {
  const [metrics, setMetrics] = useState<EvaluationMetric[]>([]);

  useEffect(() => {
    webApiClient.getEvaluationMetrics().then(setMetrics);
  }, []);

  return (
    <div className="view-container">
      <div>
        <h2 style={{ fontFamily: 'var(--font-heading)', fontSize: '20px', fontWeight: 700, margin: 0 }}>
          Evaluation System & Benchmarks
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
          Module 32 Evaluation System — Faithfulness, Relevance, Precision, and Safety Metrics
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
        {metrics.map((m) => (
          <div key={m.id} className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h4 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>{m.run_name}</h4>
              <Award size={18} style={{ color: 'var(--primary)' }} />
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block' }}>Faithfulness</span>
                <strong style={{ fontSize: '16px', color: 'var(--status-online)' }}>{(m.faithfulness_score * 100).toFixed(0)}%</strong>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block' }}>Relevance</span>
                <strong style={{ fontSize: '16px', color: 'var(--accent-cyan)' }}>{(m.relevance_score * 100).toFixed(0)}%</strong>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block' }}>Tool Precision</span>
                <strong style={{ fontSize: '16px', color: 'var(--accent-purple)' }}>{(m.tool_precision * 100).toFixed(0)}%</strong>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: 'var(--radius-md)' }}>
                <span style={{ color: 'var(--text-muted)', display: 'block' }}>Safety Score</span>
                <strong style={{ fontSize: '16px', color: 'var(--primary)' }}>{(m.safety_score * 100).toFixed(0)}%</strong>
              </div>
            </div>

            <span style={{ fontSize: '11px', color: 'var(--text-dim)', textAlign: 'right' }}>
              Avg Latency: {m.latency_avg_ms}ms
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};
