import React from "react";
import {
  MessageSquare,
  CheckSquare,
  Database,
  Calendar,
  Share2,
  Award,
  Activity,
  Settings,
} from "lucide-react";
import { useApp } from "../context/AppContext";
import { ViewType } from "../types";

export const Sidebar: React.FC = () => {
  const { activeView, setActiveView } = useApp();

  const navItems: { id: ViewType; label: string; icon: React.ReactNode }[] = [
    { id: "chat", label: "Conversation", icon: <MessageSquare size={18} /> },
    { id: "tasks", label: "Tasks & Agents", icon: <CheckSquare size={18} /> },
    { id: "memory", label: "Memory & Knowledge", icon: <Database size={18} /> },
    { id: "automations", label: "Automations", icon: <Calendar size={18} /> },
    { id: "integrations", label: "Integrations", icon: <Share2 size={18} /> },
    { id: "evaluations", label: "Evaluation System", icon: <Award size={18} /> },
    { id: "observability", label: "Observability & Audit", icon: <Activity size={18} /> },
    { id: "settings", label: "Settings", icon: <Settings size={18} /> },
  ];

  return (
    <aside className="sidebar">
      {navItems.map((item) => (
        <div
          key={item.id}
          className={`nav-item ${activeView === item.id ? "active" : ""}`}
          onClick={() => setActiveView(item.id)}
        >
          {item.icon}
          <span>{item.label}</span>
        </div>
      ))}
    </aside>
  );
};
