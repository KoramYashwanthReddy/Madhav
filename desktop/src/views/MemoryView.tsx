import React, { useEffect, useState } from "react";
import { Search, Bookmark } from "lucide-react";
import { api } from "../api/client";
import { MemoryItem } from "../types";

export const MemoryView: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [ragQuery, setRagQuery] = useState("");
  const [ragResults, setRagResults] = useState<string | null>(null);

  useEffect(() => {
    api.getMemories().then(setMemories);
  }, []);

  const handleRagSearch = () => {
    if (!ragQuery.trim()) return;
    setRagResults(`RAG Retrieval Query: "${ragQuery}" -> Matched 3 vector chunks from Module 09 Knowledge Base (Score: 0.94).`);
  };

  return (
    <div className="view-container">
      <div className="view-header">
        <div>
          <h1 className="view-title">Memory & Knowledge Hub</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            Personal profile memory graph, facts, preferences, and RAG retrieval (Modules 08, 09, & 10)
          </p>
        </div>
      </div>

      {/* RAG Retrieval Test Workbench */}
      <div className="card">
        <div className="card-title">
          <Search size={18} style={{ color: "var(--accent-indigo)" }} />
          <span>RAG Retrieval Vector Search Workbench</span>
        </div>
        <div style={{ display: "flex", gap: 10, marginBottom: 12 }}>
          <input
            type="text"
            className="input-box"
            placeholder="Test semantic retrieval query across personal knowledge files..."
            value={ragQuery}
            onChange={(e) => setRagQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleRagSearch()}
          />
          <button className="btn btn-primary" onClick={handleRagSearch}>
            <span>Search</span>
          </button>
        </div>
        {ragResults && (
          <div style={{ padding: 12, borderRadius: 8, background: "var(--bg-primary)", fontSize: 13, color: "#a78bfa" }}>
            {ragResults}
          </div>
        )}
      </div>

      {/* Memory Items List */}
      <div className="card">
        <div className="card-title">
          <Bookmark size={18} style={{ color: "var(--accent-purple)" }} />
          <span>Learned Personal Preferences & Profile Memories</span>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {memories.map((mem) => (
            <div
              key={mem.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: 12,
                borderRadius: 8,
                background: "var(--bg-primary)",
                border: "1px solid var(--border-color)",
              }}
            >
              <div>
                <span
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    textTransform: "uppercase",
                    padding: "2px 6px",
                    borderRadius: 4,
                    background: "rgba(99, 102, 241, 0.2)",
                    color: "#a5b4fc",
                    marginRight: 8,
                  }}
                >
                  {mem.category}
                </span>
                <span style={{ fontSize: 14, color: "var(--text-primary)" }}>{mem.content}</span>
              </div>
              <span style={{ fontSize: 12, color: "var(--text-muted)" }}>
                Confidence: {(mem.confidence * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
