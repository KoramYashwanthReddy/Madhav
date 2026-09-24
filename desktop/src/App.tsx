import React from "react";
import { AppProvider, useApp } from "./context/AppContext";
import { Header } from "./components/Header";
import { Sidebar } from "./components/Sidebar";
import { QuickOverlay } from "./components/QuickOverlay";
import { ApprovalModal } from "./components/ApprovalModal";

import { ChatView } from "./views/ChatView";
import { TasksView } from "./views/TasksView";
import { MemoryView } from "./views/MemoryView";
import { AutomationsView } from "./views/AutomationsView";
import { IntegrationsView } from "./views/IntegrationsView";
import { EvaluationView } from "./views/EvaluationView";
import { ObservabilityView } from "./views/ObservabilityView";
import { SettingsView } from "./views/SettingsView";

const AppContent: React.FC = () => {
  const { activeView, isOverlayMode } = useApp();

  if (isOverlayMode) {
    return <QuickOverlay />;
  }

  const renderView = () => {
    switch (activeView) {
      case "chat":
        return <ChatView />;
      case "tasks":
        return <TasksView />;
      case "memory":
        return <MemoryView />;
      case "automations":
        return <AutomationsView />;
      case "integrations":
        return <IntegrationsView />;
      case "evaluations":
        return <EvaluationView />;
      case "observability":
        return <ObservabilityView />;
      case "settings":
        return <SettingsView />;
      default:
        return <ChatView />;
    }
  };

  return (
    <div className="app-container">
      <Header />
      <div className="app-main">
        <Sidebar />
        <main className="content-area">{renderView()}</main>
      </div>
      <ApprovalModal />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
};

export default App;
