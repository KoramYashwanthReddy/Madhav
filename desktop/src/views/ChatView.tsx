import React, { useState } from "react";
import { Send, Bot, User, Cpu, Wrench, Shield, ChevronDown, ChevronUp } from "lucide-react";
import { api } from "../api/client";
import { Message } from "../types";

export const ChatView: React.FC = () => {
  const [input, setInput] = useState("");
  const [selectedModel, setSelectedModel] = useState("gemini-2.5-flash");
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "msg-1",
      role: "assistant",
      content: "Hello! I am MAX, your personal AI operating layer. How can I assist you today?",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isSending, setIsSending] = useState(false);
  const [expandedReasoning, setExpandedReasoning] = useState<Record<string, boolean>>({});

  const toggleReasoning = (id: string) => {
    setExpandedReasoning((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSend = async () => {
    if (!input.trim() || isSending) return;

    const userMsg: Message = {
      id: `usr-${Date.now()}`,
      role: "user",
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsSending(true);

    try {
      const resp = await api.sendMessage("conv-default", userMsg.content, selectedModel);
      setMessages((prev) => [...prev, resp]);
    } catch {
      const errResp: Message = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content: "Error communicating with MAX AI Runtime. Please check backend connection.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errResp]);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="view-container" style={{ paddingBottom: 12 }}>
      <div className="view-header">
        <div>
          <h1 className="view-title">Conversation Engine</h1>
          <p style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            Direct interactive workspace connected to AI Runtime & Reasoning Engine
          </p>
        </div>

        {/* Model Selector */}
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Cpu size={16} style={{ color: "var(--accent-indigo)" }} />
          <select
            className="input-box"
            style={{ width: 180, padding: "6px 10px" }}
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
          >
            <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
            <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
            <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
            <option value="local-llama3">Local Llama 3.3</option>
          </select>
        </div>
      </div>

      {/* Messages Feed */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 16,
          overflowY: "auto",
          paddingRight: 8,
        }}
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            style={{
              display: "flex",
              gap: 12,
              alignSelf: msg.role === "user" ? "flex-end" : "flex-start",
              maxWidth: "85%",
            }}
          >
            {msg.role === "assistant" && (
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "var(--gradient-primary)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#fff",
                }}
              >
                <Bot size={18} />
              </div>
            )}

            <div
              style={{
                background: msg.role === "user" ? "var(--accent-indigo)" : "var(--bg-surface)",
                color: "#ffffff",
                padding: "12px 16px",
                borderRadius: 12,
                border: msg.role === "user" ? "none" : "1px solid var(--border-color)",
                fontSize: 14,
                lineHeight: 1.5,
              }}
            >
              {msg.content}

              {/* Tools Badges */}
              {msg.tools_used && msg.tools_used.length > 0 && (
                <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
                  {msg.tools_used.map((tool) => (
                    <span
                      key={tool}
                      style={{
                        fontSize: 11,
                        background: "rgba(139, 92, 246, 0.2)",
                        color: "#c4b5fd",
                        padding: "2px 8px",
                        borderRadius: 4,
                        display: "flex",
                        alignItems: "center",
                        gap: 4,
                      }}
                    >
                      <Wrench size={10} />
                      {tool}
                    </span>
                  ))}
                </div>
              )}

              {/* Reasoning Accordion */}
              {msg.reasoning && (
                <div style={{ marginTop: 10, paddingTop: 8, borderTop: "1px solid rgba(255,255,255,0.1)" }}>
                  <button
                    onClick={() => toggleReasoning(msg.id)}
                    style={{
                      background: "none",
                      border: "none",
                      color: "var(--text-secondary)",
                      fontSize: 12,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                    }}
                  >
                    <Shield size={12} />
                    <span>Reasoning Chain</span>
                    {expandedReasoning[msg.id] ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
                  </button>
                  {expandedReasoning[msg.id] && (
                    <pre
                      style={{
                        marginTop: 6,
                        fontFamily: "var(--font-family-mono)",
                        fontSize: 11,
                        color: "var(--text-secondary)",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {msg.reasoning}
                    </pre>
                  )}
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div
                style={{
                  width: 32,
                  height: 32,
                  borderRadius: "50%",
                  background: "var(--bg-surface-hover)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#fff",
                }}
              >
                <User size={18} />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Prompt Input Footer */}
      <div style={{ display: "flex", gap: 10, marginTop: 12 }}>
        <input
          type="text"
          className="input-box"
          placeholder="Type your instruction or question for MAX..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
        />
        <button className="btn btn-primary" onClick={handleSend} disabled={isSending}>
          <Send size={16} />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
};
