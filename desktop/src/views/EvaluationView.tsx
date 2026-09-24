import React, { useState } from "react";
import { Award, Play, TrendingUp } from "lucide-react";
import { EvaluationReport } from "../types";

export const EvaluationView: React.FC = () => {
  const [reports] = useState<EvaluationReport[]>([
    {
      id: "eval-1",
      suite_name: "Reasoning & Planning Benchmark Suite",
      total_cases: 50,
      passed_cases: 49,
      score: 0.98,
      created_at: new Date().toISOString(),
    },
    {
      id: "eval-2",
      suite_name: "Tool Permission Security Boundary Test Suite",
      total_cases: 30,
      passed_cases: 30,
      score: 1.0,
      created_at: new Date().toISOString(),
    },
    {
      id: "eval-3",
      suite_name: "RAG Retrieval Precision & Recall Evaluation",
      total_cases: 40,
      passed_cases: 38,
      score: 0.95,
      created_at: new Date().toISOString(),
    },
  ]);

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">Evaluation System Workbench</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            Automated quality benchmarks, LLM judge scoring, and regression tracking (Module 32)
          </p>
        </div>
        <button className="btn btn-primary">
          <Play size={14} />
          <span>Run All Benchmarks</span>
        </button>
      </div>

      <div className="card">
        <div className="card-title">
          <Award size={18} style={{ color: "var(--accent-indigo)" }} />
          <span>Latest Evaluation Suite Reports</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {reports.map((rep) => (
            <div
              key={rep.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: 14,
                borderRadius: 8,
                background: "var(--bg-primary)",
                border: "1px solid var(--border-color)",
              }}
            >
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{rep.suite_name}</div>
                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>
                  Passed: {rep.passed_cases} / {rep.total_cases} cases ({rep.created_at.slice(0, 10)})
                </div>
              </div>

              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 18, fontWeight: 700, color: "var(--status-success)" }}>
                  {(rep.score * 100).toFixed(1)}%
                </div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", display: "flex", alignItems: "center", gap: 2 }}>
                  <TrendingUp size={10} />
                  <span>No Regression</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
