import React from 'react';
import { WebAppProvider, useWebApp } from './context/WebAppContext';
import { Header } from './components/Header';
import { Sidebar } from './components/Sidebar';
import { QuickCommandPalette } from './components/QuickCommandPalette';
import { ApprovalModal } from './components/ApprovalModal';
import { NotificationDrawer } from './components/NotificationDrawer';

import { HomeView } from './views/HomeView';
import { ChatView } from './views/ChatView';
import { TasksView } from './views/TasksView';
import { AutomationsView } from './views/AutomationsView';
import { MemoryView } from './views/MemoryView';
import { KnowledgeView } from './views/KnowledgeView';
import { AgentsView } from './views/AgentsView';
import { ToolsView } from './views/ToolsView';
import { IntegrationsView } from './views/IntegrationsView';
import { NotificationsView } from './views/NotificationsView';
import { ActivityView } from './views/ActivityView';
import { EvaluationsView } from './views/EvaluationsView';
import { SystemView } from './views/SystemView';
import { SettingsView } from './views/SettingsView';

const MainLayout: React.FC = () => {
  const { activeSection } = useWebApp();

  const renderActiveView = () => {
    switch (activeSection) {
      case 'home':
        return <HomeView />;
      case 'chat':
        return <ChatView />;
      case 'tasks':
        return <TasksView />;
      case 'automations':
        return <AutomationsView />;
      case 'memory':
        return <MemoryView />;
      case 'knowledge':
        return <KnowledgeView />;
      case 'agents':
        return <AgentsView />;
      case 'tools':
        return <ToolsView />;
      case 'integrations':
        return <IntegrationsView />;
      case 'notifications':
        return <NotificationsView />;
      case 'activity':
        return <ActivityView />;
      case 'evaluations':
        return <EvaluationsView />;
      case 'system':
        return <SystemView />;
      case 'settings':
        return <SettingsView />;
      default:
        return <HomeView />;
    }
  };

  return (
    <div className="app-container">
      <Header />
      <div className="app-main-layout">
        <Sidebar />
        <main style={{ flex: 1, height: '100%', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {renderActiveView()}
        </main>
      </div>

      <QuickCommandPalette />
      <ApprovalModal />
      <NotificationDrawer />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <WebAppProvider>
      <MainLayout />
    </WebAppProvider>
  );
};

export default App;
