import React, { useState } from "react";
import { Mic, Send, Sparkles, X } from "lucide-react";
import { toggleOverlayWindowNative } from "../api/tauri_bridge";

export const QuickOverlay: React.FC = () => {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<string | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleClose = async () => {
    await toggleOverlayWindowNative();
  };

  const handleExecute = () => {
    if (!query.trim()) return;
    setIsProcessing(true);
    setResult(null);

    setTimeout(() => {
      setResult(`Executed quick HUD command: "${query}". Task delegated to AI Runtime.`);
      setIsProcessing(false);
    }, 800);
  };

  return (
    <div className="overlay-container">
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, fontWeight: 700, fontSize: 16, color: "#8b5cf6" }}>
          <Sparkles size={20} />
          <span>MAX Quick HUD</span>
        </div>
        <button className="btn btn-secondary" style={{ padding: 6 }} onClick={handleClose}>
          <X size={16} />
        </button>
      </div>

      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        <input
          type="text"
          className="input-box"
          placeholder="Ask Max anything or trigger an instant command... (Press Enter)"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleExecute()}
          autoFocus
        />
        <button className="btn btn-secondary" style={{ padding: "0 12px" }}>
          <Mic size={18} />
        </button>
        <button className="btn btn-primary" onClick={handleExecute} disabled={isProcessing}>
          <Send size={16} />
        </button>
      </div>

      {isProcessing && (
        <div style={{ padding: 12, borderRadius: 8, background: "rgba(99, 102, 241, 0.1)", color: "#a5b4fc", fontSize: 13 }}>
          Processing prompt with MAX Reasoning Engine...
        </div>
      )}

      {result && (
        <div style={{ padding: 14, borderRadius: 8, background: "var(--bg-surface)", border: "1px solid var(--border-color)", fontSize: 14 }}>
          {result}
        </div>
      )}
    </div>
  );
};
